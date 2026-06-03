import os
import tkinter as tk
from tkinter import ttk
from config.constants import Config

class SuccessDialog:
    """
    导出成功提示框。
    
    封装导出成功后的视觉反馈界面，包含打勾徽章、只读路径展示以及快捷打开目录功能。
    """
    def __init__(self, parent, out_path, export_dir):
        """
        初始化对话框并配置模态交互。
        """
        self.dlg = tk.Toplevel(parent)
        self.dlg.title("导出成功")
        self.dlg.transient(parent)
        
        # 禁用父窗口以实现模态，并避免 grab_set() 导致任务栏最小化失效问题
        try:
            parent.attributes("-disabled", True)
        except Exception:
            pass
            
        def restore_parent(event):
            if event.widget == self.dlg:
                try:
                    parent.attributes("-disabled", False)
                except Exception:
                    pass
        self.dlg.bind("<Destroy>", restore_parent)
        
        self.dlg.configure(bg=Config.COLORS['main_bg'])
        self.out_path = out_path
        self.export_dir = export_dir
        
        # 1. 窗口几何位置初始化
        self._setup_geometry(parent)
        
        # 2. 界面主体与内容渲染
        self._build_layout()
        
    def _setup_geometry(self, parent):
        """ 配置窗口居中与大小 """
        w = Config.LAYOUT['success_dialog_w']
        h = Config.LAYOUT['success_dialog_h']
        sw, sh = parent.winfo_screenwidth(), parent.winfo_screenheight()
        
        self.dlg.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        self.dlg.resizable(False, False)

    def _build_layout(self):
        """ 构建各区域容器与小部件 """
        pad = Config.LAYOUT['success_dialog_pad']
        main_frame = tk.Frame(self.dlg, bg=Config.COLORS['main_bg'], padx=pad, pady=pad)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 1. 物理层级安排：先布局底部按钮，防止随缩放被遮挡
        btn_frame = tk.Frame(main_frame, bg=Config.COLORS['main_bg'])
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self._setup_buttons(btn_frame)
        
        # 2. 顶部徽章和状态描述
        top_bar = tk.Frame(main_frame, bg=Config.COLORS['main_bg'])
        top_bar.pack(side=tk.TOP, fill=tk.X, expand=True)
        self._draw_status_badge(top_bar)
        
        # 3. 中间路径只读展示文本框
        path_entry = ttk.Entry(main_frame, font=Config.FONTS['combo'], justify="left")
        path_entry.pack(fill=tk.X, pady=(12, 18))
        path_entry.insert(0, self.out_path)
        path_entry.config(state="readonly")

    def _draw_status_badge(self, parent):
        """ 绘制打勾状态状态徽章及文字描述 """
        icon_sz = Config.LAYOUT['success_icon_size']
        try:
            icon_cv = tk.Canvas(parent, width=icon_sz, height=icon_sz, bg=Config.COLORS['main_bg'], highlightthickness=0)
            icon_cv.pack(side=tk.LEFT, anchor="n", padx=(0, 16))
            
            # 绘制绿色实心背景圆
            icon_cv.create_oval(2, 2, icon_sz - 2, icon_sz - 2, fill="#10b981", outline="")
            
            # 画白色粗线条打勾，端点圆润
            icon_cv.create_line(icon_sz * 0.28, icon_sz * 0.5, icon_sz * 0.45, icon_sz * 0.68, fill="white", width=3, capstyle=tk.ROUND)
            icon_cv.create_line(icon_sz * 0.45, icon_sz * 0.68, icon_sz * 0.72, icon_sz * 0.32, fill="white", width=3, capstyle=tk.ROUND)
        except Exception:
            pass
            
        txt_frame = tk.Frame(parent, bg=Config.COLORS['main_bg'])
        txt_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        ttk.Label(txt_frame, text="导出成功！", font=Config.FONTS['side_title'], background=Config.COLORS['main_bg']).pack(anchor="w", pady=(0, 4))
        ttk.Label(txt_frame, text="您的文件已保存至本地：", font=Config.FONTS['zh_normal'], background=Config.COLORS['main_bg'], foreground="#64748b").pack(anchor="w")

    def _setup_buttons(self, parent):
        """ 配置确认与打开目录按钮 """
        ttk.Button(
            parent,
            text=" 好的 ",
            command=self.dlg.destroy
        ).pack(side=tk.RIGHT, padx=(12, 0))
        
        def open_dir():
            self.dlg.destroy()
            import subprocess
            try:
                norm_path = os.path.normpath(self.out_path)
                subprocess.run(f'explorer /select,"{norm_path}"', shell=True)
            except Exception:
                try:
                    os.startfile(self.export_dir)
                except Exception:
                    pass
                    
        ttk.Button(
            parent,
            text="打开当前导出目录",
            command=open_dir,
            style='Action.TButton'
        ).pack(side=tk.RIGHT)
