"""
IceZoom — Hotkey Manager  (thread-safe, zero-latency mouse hook)
================================================================
Architecture
------------
All combo evaluation happens on the global hook background threads.
Results are posted to the Qt main thread exclusively via pyqtSignal
(Qt auto-connection queues the call across thread boundaries), so no
Qt timer, widget, or UI object is ever touched from a hook callback.

Mouse hook — why we bypass the `mouse` library
-----------------------------------------------
The `mouse` library (v0.7.1) uses Windows' WH_MOUSE_LL low-level hook,
but forwards events through a Python Queue to a second processing thread.
This two-thread relay introduces latency.  Windows enforces a hard 300 ms
deadline for WH_MOUSE_LL hook procs: if CallNextHookEx is not called
within that window the OS silently removes the hook and stops delivering
events.  When a keyboard modifier is simultaneously held, the `keyboard`
library's own hook thread competes for the GIL and our application's lock,
which can push mouse-queue processing past the 300 ms limit — causing
the "drops RMB while Shift is held" symptom.

The fix: install a direct WH_MOUSE_LL hook via ctypes on a dedicated
message-pump thread.  The Win32 callback does the absolute minimum
(read wParam, store token in a deque, call CallNextHookEx) and returns
in microseconds.  A separate evaluation thread drains the deque and
runs the binding checks, keeping the hook proc itself under 1 ms.

Keyboard hook
-------------
The `keyboard` library is reliable for key events and is kept as-is.
Its hook callback updates `_pressed_keys` and calls `_evaluate_bindings`.

Modifier key normalisation
--------------------------
  "left shift" / "right shift"  → "shift"
  "left ctrl"  / "right ctrl"   → "ctrl"
  "left alt"   / "right alt"    → "alt"
  "left windows" / "right windows" → "win"
  Localised variants ("skift" etc.) → canonical English form

Supported mouse tokens (case-insensitive in combo strings):
  Mouse_LMB        — left mouse button
  Mouse_RMB        — right mouse button
  Mouse_MMB        — middle mouse button
  Mouse_Scroll_Up  — scroll wheel up
  Mouse_Scroll_Down — scroll wheel down

Scroll tokens are ephemeral: press-actions only (no hold-actions).
"""
import ctypes
import ctypes.wintypes
import threading
import collections
from typing import Dict, Set, Deque, Tuple, Optional

import keyboard
from PyQt6.QtCore import QObject, pyqtSignal


# ── Win32 constants & types ───────────────────────────────────────────────────
_WH_MOUSE_LL    = 14
_WM_MOUSEMOVE   = 0x0200
_WM_LBUTTONDOWN = 0x0201
_WM_LBUTTONUP   = 0x0202
_WM_RBUTTONDOWN = 0x0204
_WM_RBUTTONUP   = 0x0205
_WM_MBUTTONDOWN = 0x0207
_WM_MBUTTONUP   = 0x0208
_WM_MOUSEWHEEL  = 0x020A

_WHEEL_DELTA = 120

_user32   = ctypes.WinDLL("user32", use_last_error=True)
_kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

class _MSLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("x",        ctypes.c_long),
        ("y",        ctypes.c_long),
        ("mouseData", ctypes.c_int32),
        ("flags",    ctypes.wintypes.DWORD),
        ("time",     ctypes.c_int),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]

_HOOKPROC = ctypes.CFUNCTYPE(
    ctypes.c_int,
    ctypes.c_int,
    ctypes.wintypes.WPARAM,
    ctypes.POINTER(_MSLLHOOKSTRUCT),
)

# wParam → (token, is_down, is_ephemeral)
_WM_TO_TOKEN: Dict[int, Tuple[str, bool, bool]] = {
    _WM_LBUTTONDOWN: ("mouse_lmb", True,  False),
    _WM_LBUTTONUP:   ("mouse_lmb", False, False),
    _WM_RBUTTONDOWN: ("mouse_rmb", True,  False),
    _WM_RBUTTONUP:   ("mouse_rmb", False, False),
    _WM_MBUTTONDOWN: ("mouse_mmb", True,  False),
    _WM_MBUTTONUP:   ("mouse_mmb", False, False),
}

_SCROLL_UP_TOKEN   = "mouse_scroll_up"
_SCROLL_DOWN_TOKEN = "mouse_scroll_down"
_EPHEMERAL_TOKENS: Set[str] = {_SCROLL_UP_TOKEN, _SCROLL_DOWN_TOKEN}


# ── Modifier alias map ────────────────────────────────────────────────────────
_MODIFIER_ALIASES: Dict[str, str] = {
    "left shift":    "shift",
    "right shift":   "shift",
    "left ctrl":     "ctrl",
    "right ctrl":    "ctrl",
    "left control":  "ctrl",
    "right control": "ctrl",
    "left alt":      "alt",
    "right alt":     "alt",
    "left windows":  "win",
    "right windows": "win",
    "left win":      "win",
    "right win":     "win",
    # Localised variants
    "skift":         "shift",
    "venstre skift": "shift",
    "højre skift":   "shift",
    "venstre ctrl":  "ctrl",
    "højre ctrl":    "ctrl",
    "venstre alt":   "alt",
    "højre alt":     "alt",
    "umschalt":      "shift",
    "maj":           "shift",
}


def _normalise_token(token: str) -> str:
    t = token.strip().lower()
    return _MODIFIER_ALIASES.get(t, t)


def _parse_combo(combo: str) -> frozenset:
    return frozenset(_normalise_token(p) for p in combo.split("+") if p.strip())


# ── Low-level mouse hook (runs on its own dedicated thread) ───────────────────

class _DirectMouseHook:
    """
    Installs a WH_MOUSE_LL hook on a dedicated Win32 message-pump thread.

    The hook proc does the absolute minimum — it reads wParam, appends a
    small named-tuple to a lock-free deque, then calls CallNextHookEx and
    returns immediately.  This guarantees we never exceed the 300 ms
    Windows deadline, even when a keyboard modifier is simultaneously held.

    A separate evaluation thread drains the deque and calls the user-
    supplied callback.
    """

    _MouseEvt = collections.namedtuple("_MouseEvt", ["token", "is_down", "ephemeral"])

    def __init__(self, callback):
        """
        callback(token: str, is_down: bool, ephemeral_token: str | None)
        is called from the evaluation thread for each mouse button/scroll event.
        """
        self._callback  = callback
        self._hook      = None
        self._hookproc  = None   # keep a reference so GC doesn't collect the CFUNCTYPE
        self._thread    = None
        self._eval_thread = None
        self._thread_id = None
        self._running   = False
        # Lock-free producer→consumer: hook proc writes, eval thread reads
        self._deque: Deque = collections.deque()
        self._event_available = threading.Event()

    # ── Start / Stop ─────────────────────────────────────────────────────────

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._message_pump, name="MouseHookPump", daemon=True
        )
        self._eval_thread = threading.Thread(
            target=self._eval_loop, name="MouseHookEval", daemon=True
        )
        self._thread.start()
        self._eval_thread.start()

    def stop(self):
        self._running = False
        # Wake the eval thread so it can exit
        self._event_available.set()
        # Post WM_QUIT to the pump thread to exit GetMessage
        if self._thread_id is not None:
            _user32.PostThreadMessageW(self._thread_id, 0x0012, 0, 0)  # WM_QUIT

    # ── Message pump thread: installs hook, runs GetMessage loop ─────────────

    def _message_pump(self):
        self._thread_id = _kernel32.GetCurrentThreadId()

        def _hook_proc(nCode, wParam, lParam):
            if nCode >= 0:
                wp = wParam
                if wp == _WM_MOUSEWHEEL:
                    struct = lParam.contents
                    # High word of mouseData is the wheel delta (signed short)
                    delta = ctypes.c_short(struct.mouseData >> 16).value
                    tok = _SCROLL_UP_TOKEN if delta > 0 else _SCROLL_DOWN_TOKEN
                    self._deque.append(
                        _DirectMouseHook._MouseEvt(tok, True, tok)
                    )
                    self._event_available.set()
                elif wp in _WM_TO_TOKEN:
                    token, is_down, _ = _WM_TO_TOKEN[wp]
                    self._deque.append(
                        _DirectMouseHook._MouseEvt(token, is_down, None)
                    )
                    self._event_available.set()
            # MUST call immediately — this is why we do zero blocking work here
            return _user32.CallNextHookEx(None, nCode, wParam, lParam)

        self._hookproc = _HOOKPROC(_hook_proc)
        self._hook = _user32.SetWindowsHookExW(
            _WH_MOUSE_LL, self._hookproc, None, 0
        )

        # Standard Win32 message pump — keeps the hook alive
        msg = ctypes.wintypes.MSG()
        while _user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
            _user32.TranslateMessage(ctypes.byref(msg))
            _user32.DispatchMessageW(ctypes.byref(msg))

        # Cleanup
        if self._hook:
            _user32.UnhookWindowsHookEx(self._hook)
            self._hook = None

    # ── Evaluation thread: drains deque and calls user callback ──────────────

    def _eval_loop(self):
        while self._running:
            self._event_available.wait()
            self._event_available.clear()
            while self._deque:
                try:
                    evt = self._deque.popleft()
                except IndexError:
                    break
                self._callback(evt.token, evt.is_down, evt.ephemeral)


# ── HotkeyManager ─────────────────────────────────────────────────────────────

class HotkeyManager(QObject):
    """
    Manages global hotkey registration for IceZoom actions.

    Signals
    -------
    action_triggered(action_id: str)   — rising edge of a press combo
    action_held_start(action_id: str)  — hold combo becomes satisfied
    action_held_end(action_id: str)    — hold combo is no longer satisfied

    Thread safety
    -------------
    Hook callbacks run on background threads.  `_pressed_keys`, `_held_state`,
    `_prev_satisfied`, and `_bindings` are all guarded by `_lock`.  Signals are
    emitted *outside* the lock; Qt auto-connection queues them to the main thread.
    """

    action_triggered  = pyqtSignal(str)
    action_held_start = pyqtSignal(str)
    action_held_end   = pyqtSignal(str)

    _HOLD_ACTIONS: Set[str] = {"toggle_zoom_hold"}

    def __init__(self, parent=None):
        super().__init__(parent)

        self._lock = threading.Lock()
        self._enabled         = True
        self._bindings:       Dict[str, str]  = {}
        self._pressed_keys:   Set[str]        = set()
        self._held_state:     Dict[str, bool] = {}
        self._prev_satisfied: Dict[str, bool] = {}

        self._kb_hook    = None
        self._mouse_hook: Optional[_DirectMouseHook] = None
        self._hooks_active = False

    # ── Public API ────────────────────────────────────────────────────────────

    def load_bindings(self, bindings: Dict[str, str]):
        with self._lock:
            self._bindings        = dict(bindings)
            self._held_state      = {a: False for a in self._bindings}
            self._prev_satisfied  = {a: False for a in self._bindings}
        self._install_hooks()

    def update_binding(self, action_id: str, combo: str):
        with self._lock:
            self._bindings[action_id]       = combo
            self._held_state[action_id]     = False
            self._prev_satisfied[action_id] = False

    def set_enabled(self, enabled: bool):
        holds_to_release = []
        with self._lock:
            if not enabled:
                for aid, held in list(self._held_state.items()):
                    if held:
                        self._held_state[aid] = False
                        holds_to_release.append(aid)
            self._enabled = enabled
        for aid in holds_to_release:
            self.action_held_end.emit(aid)

    def is_enabled(self) -> bool:
        with self._lock:
            return self._enabled

    def toggle_enabled(self) -> bool:
        with self._lock:
            self._enabled = not self._enabled
            return self._enabled

    def cleanup(self):
        self._remove_hooks()

    # ── Hook management ───────────────────────────────────────────────────────

    def _install_hooks(self):
        self._remove_hooks()

        # Keyboard hook via `keyboard` library (reliable for key events)
        try:
            self._kb_hook = keyboard.hook(self._on_kb_event, suppress=False)
        except Exception as e:
            print(f"[HotkeyManager] keyboard.hook failed: {e}")

        # Mouse hook via direct Win32 ctypes (bypasses mouse library queue)
        try:
            self._mouse_hook = _DirectMouseHook(self._on_mouse_event_direct)
            self._mouse_hook.start()
        except Exception as e:
            print(f"[HotkeyManager] DirectMouseHook failed: {e}")

        self._hooks_active = True

    def _remove_hooks(self):
        if self._kb_hook is not None:
            try:
                keyboard.unhook(self._kb_hook)
            except Exception:
                pass
            self._kb_hook = None

        if self._mouse_hook is not None:
            try:
                self._mouse_hook.stop()
            except Exception:
                pass
            self._mouse_hook = None

        with self._lock:
            self._pressed_keys.clear()
        self._hooks_active = False

    # ── Keyboard hook callback ────────────────────────────────────────────────

    def _on_kb_event(self, event):
        token = _normalise_token(event.name) if event.name else None
        if not token or token in ("unknown", ""):
            return

        with self._lock:
            if event.event_type == keyboard.KEY_DOWN:
                self._pressed_keys.add(token)
            elif event.event_type == keyboard.KEY_UP:
                self._pressed_keys.discard(token)
            snapshot = frozenset(self._pressed_keys)
            enabled  = self._enabled

        if enabled:
            self._evaluate_bindings(snapshot, ephemeral_token=None)

    # ── Mouse hook callback (called from _DirectMouseHook eval thread) ────────

    def _on_mouse_event_direct(self, token: str, is_down: bool,
                                ephemeral_token: Optional[str]):
        """
        Called by _DirectMouseHook._eval_loop for every button / scroll event.

        For button events:
          is_down=True  → add token to pressed set
          is_down=False → ALWAYS discard token, even if we somehow missed the
                          corresponding DOWN (guarantees RMB state is cleared)

        For scroll events (ephemeral_token is not None):
          token is added then immediately removed (ephemeral).
        """
        with self._lock:
            if ephemeral_token:
                # Scroll — add temporarily for the snapshot, then remove
                self._pressed_keys.add(token)
                snapshot = frozenset(self._pressed_keys)
                self._pressed_keys.discard(token)
            else:
                if is_down:
                    self._pressed_keys.add(token)
                else:
                    # Force-clear on every UP regardless of whether we saw DOWN.
                    # This is the key fix: if the DOWN was somehow missed (e.g.
                    # during a hook re-installation), the UP still resets state.
                    self._pressed_keys.discard(token)
                snapshot = frozenset(self._pressed_keys)
            enabled = self._enabled

        if enabled:
            self._evaluate_bindings(
                snapshot,
                ephemeral_token=ephemeral_token,
            )

    # ── Combo evaluation ──────────────────────────────────────────────────────

    def _evaluate_bindings(self, snapshot: frozenset, ephemeral_token):
        """
        Checks every registered binding against `snapshot`.

        Hold actions  → emit held_start / held_end on state transitions.
        Press actions → emit triggered on the rising edge only.
        Ephemeral (scroll) tokens → press-actions only, never hold-actions.

        All emits happen *outside* the lock so no slot can re-enter while
        the lock is held.  Qt auto-connection queues them to the main thread.
        """
        to_emit = []

        with self._lock:
            bindings_snapshot = dict(self._bindings)

        for action_id, combo_str in bindings_snapshot.items():
            if not combo_str:
                continue

            required  = _parse_combo(combo_str)
            satisfied = required.issubset(snapshot)
            is_hold   = action_id in self._HOLD_ACTIONS

            if ephemeral_token and is_hold:
                continue

            with self._lock:
                if is_hold:
                    prev = self._held_state.get(action_id, False)
                    if satisfied and not prev:
                        self._held_state[action_id] = True
                        to_emit.append(("held_start", action_id))
                    elif not satisfied and prev:
                        self._held_state[action_id] = False
                        to_emit.append(("held_end", action_id))
                else:
                    prev = self._prev_satisfied.get(action_id, False)
                    if satisfied and not prev:
                        to_emit.append(("triggered", action_id))
                    self._prev_satisfied[action_id] = satisfied

        for signal_name, action_id in to_emit:
            if signal_name == "triggered":
                self.action_triggered.emit(action_id)
            elif signal_name == "held_start":
                self.action_held_start.emit(action_id)
            elif signal_name == "held_end":
                self.action_held_end.emit(action_id)
