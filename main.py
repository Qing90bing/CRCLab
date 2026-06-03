import ctypes
import tkinter as tk
from view.main_window import CRCLabApp

if __name__ == "__main__":
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    root = tk.Tk()
    app = CRCLabApp(root)
    root.mainloop()

