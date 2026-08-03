import ctypes
import tkinter as tk

from view.main_window import CRCLabApp

if __name__ == "__main__":
    # 1. 尝试开启 DPI 感知，交由操作系统和 Tkinter 原生引擎协同处理
    # 彻底移除手动计算的 root.tk.call('tk', 'scaling')，避免与用户的 Windows 兼容性设置发生"双重放大"冲突！
    try:
        # Windows 10 及以上
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            # Windows 8.1
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            try:  # noqa: SIM105  # fallback chain for DPI awareness
                # Windows Vista/7
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass

    root = tk.Tk()
    app = CRCLabApp(root)
    root.mainloop()
