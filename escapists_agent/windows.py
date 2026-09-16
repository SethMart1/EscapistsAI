"""Win32 client capture and normal scan-code input; no game memory access."""
import ctypes as C
from ctypes import wintypes as W
import os
import time
import numpy as np
from PIL import ImageGrab


class Windows:
    def __init__(self):
        if os.name != 'nt':
            raise RuntimeError('Live capture requires Windows')
        self.u = C.WinDLL('user32', use_last_error=True)
        self.u.GetForegroundWindow.restype = W.HWND
        self.u.IsWindow.argtypes = [W.HWND]
        self.u.IsWindowVisible.argtypes = [W.HWND]
        self.u.IsIconic.argtypes = [W.HWND]
        self.u.GetClientRect.argtypes = [W.HWND,C.POINTER(W.RECT)]
        self.u.ClientToScreen.argtypes = [W.HWND,C.POINTER(W.POINT)]
        self.u.GetWindowTextW.argtypes = [W.HWND,W.LPWSTR,C.c_int]
        self.u.GetAsyncKeyState.argtypes = [C.c_int]
        self.u.GetAsyncKeyState.restype = C.c_short
        try:
            self.u.SetProcessDpiAwarenessContext.argtypes = [C.c_void_p]
            self.u.SetProcessDpiAwarenessContext(C.c_void_p(-4))
        except AttributeError:
            self.u.SetProcessDPIAware()

    def windows(self):
        found = []
        callback_type = C.WINFUNCTYPE(W.BOOL,W.HWND,W.LPARAM)
        def visit(hwnd, _):
            title = C.create_unicode_buffer(1024)
            self.u.GetWindowTextW(hwnd,title,len(title))
            if title.value and self.u.IsWindowVisible(hwnd):
                found.append((int(hwnd),title.value))
            return True
        self.u.EnumWindows.argtypes = [callback_type,W.LPARAM]
        self.u.EnumWindows(callback_type(visit),0)
        return found

    def find(self, title):
        matches = [(h,t) for h,t in self.windows() if t.casefold()==title.casefold()]
        if len(matches)!=1:
            raise RuntimeError(f'Expected one exact window title {title!r}; found {len(matches)}. Run windows.')
        return matches[0][0]

    def ready(self, hwnd):
        return bool(self.u.IsWindow(hwnd) and self.u.IsWindowVisible(hwnd)
                    and not self.u.IsIconic(hwnd) and self.u.GetForegroundWindow()==hwnd)

    def stop_pressed(self):
        return bool(self.u.GetAsyncKeyState(0x77)&0x8000)  # F8

    def capture(self, hwnd):
        if not self.ready(hwnd):
            raise RuntimeError('Game must be foreground, visible and not minimized')
        rect, point = W.RECT(), W.POINT(0,0)
        if not self.u.GetClientRect(hwnd,C.byref(rect)) or not self.u.ClientToScreen(hwnd,C.byref(point)):
            raise C.WinError(C.get_last_error())
        if rect.right < 32 or rect.bottom < 32:
            raise RuntimeError('Game client area is too small')
        frame = np.array(ImageGrab.grab(bbox=(point.x,point.y,point.x+rect.right,point.y+rect.bottom),all_screens=True).convert('RGB'))
        if not self.ready(hwnd):
            raise RuntimeError('Focus changed during capture')
        return frame


class KEYBDINPUT(C.Structure):
    _fields_ = [('wVk',W.WORD),('wScan',W.WORD),('dwFlags',W.DWORD),('time',W.DWORD),('dwExtraInfo',C.c_size_t)]


class MOUSEINPUT(C.Structure):
    _fields_ = [('dx',W.LONG),('dy',W.LONG),('mouseData',W.DWORD),('dwFlags',W.DWORD),('time',W.DWORD),('dwExtraInfo',C.c_size_t)]


class INPUTUNION(C.Union):
    _fields_ = [('ki',KEYBDINPUT),('mi',MOUSEINPUT)]


class INPUT(C.Structure):
    _anonymous_ = ('value',)
    _fields_ = [('type',W.DWORD),('value',INPUTUNION)]


class InputController:
    SCANS = {'w':0x11,'a':0x1e,'s':0x1f,'d':0x20}

    def __init__(self, windows, hwnd, armed=False, stop_file=None):
        self.windows,self.hwnd,self.armed = windows,hwnd,armed
        self.stop_file = stop_file
        self.held = set()

    def safe(self):
        return (self.windows.ready(self.hwnd) and not self.windows.stop_pressed()
                and not (self.stop_file and self.stop_file.exists()))

    def send(self, key, up):
        event = INPUT(type=1,ki=KEYBDINPUT(0,self.SCANS[key],0x0008 | (0x0002 if up else 0),0,0))
        self.windows.u.SendInput.argtypes = [W.UINT,C.POINTER(INPUT),C.c_int]
        if self.windows.u.SendInput(1,C.byref(event),C.sizeof(INPUT))!=1:
            raise RuntimeError('Windows rejected input (check game privilege level)')

    def release(self):
        errors=[]
        for key in list(self.held):
            try:
                self.send(key,True)
                self.held.remove(key)
            except Exception as exc:
                errors.append(str(exc))
        if errors:
            raise RuntimeError('; '.join(errors))

    def perform(self, action, timestamp):
        if not self.armed or action.key is None:
            return
        if action.key not in self.SCANS or not 0 < action.duration <= 0.15:
            raise RuntimeError('Action exceeds movement allowlist/burst limit')
        if time.monotonic()-timestamp > 1.0 or not self.safe():
            raise RuntimeError('Stale observation, focus loss or emergency stop')
        try:
            self.held.add(action.key)
            self.send(action.key,False)
            end = time.monotonic()+action.duration
            while time.monotonic()<end:
                if not self.safe():
                    raise RuntimeError('Focus loss or emergency stop during movement')
                time.sleep(0.01)
        finally:
            self.release()
