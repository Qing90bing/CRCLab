import platform
import ctypes
from config.constants import Config

try:
    HAS_EMF_DEPENDENCY = (platform.system() == "Windows")
    if HAS_EMF_DEPENDENCY:
        class POINT(ctypes.Structure):
            _fields_ = [("x", ctypes.c_int), ("y", ctypes.c_int)]
            
        # 声明 Windows GDI32 核心接口，建立类型安全的指针映射
        gdi32 = ctypes.windll.gdi32
        
        # 第二个参数使用 c_void_p，以便安全地兼容宽字符指针与空值指针
        gdi32.CreateEnhMetaFileW.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_wchar_p]
        gdi32.CreateEnhMetaFileW.restype = ctypes.c_void_p
        
        gdi32.CloseEnhMetaFile.argtypes = [ctypes.c_void_p]
        gdi32.CloseEnhMetaFile.restype = ctypes.c_void_p
        
        gdi32.DeleteEnhMetaFile.argtypes = [ctypes.c_void_p]
        gdi32.DeleteEnhMetaFile.restype = ctypes.c_bool
        
        gdi32.GetEnhMetaFileBits.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_void_p]
        gdi32.GetEnhMetaFileBits.restype = ctypes.c_uint
        
        gdi32.Rectangle.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]
        gdi32.Rectangle.restype = ctypes.c_bool
        
        gdi32.MoveToEx.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_void_p]
        gdi32.MoveToEx.restype = ctypes.c_bool
        
        gdi32.LineTo.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
        gdi32.LineTo.restype = ctypes.c_bool
        
        # 统一路径折线绘制接口，平滑相邻折点并消除毛边
        gdi32.Polyline.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int]
        gdi32.Polyline.restype = ctypes.c_bool
        
        gdi32.CreateSolidBrush.argtypes = [ctypes.c_uint]
        gdi32.CreateSolidBrush.restype = ctypes.c_void_p
        
        gdi32.CreatePen.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_uint]
        gdi32.CreatePen.restype = ctypes.c_void_p
        
        gdi32.SelectObject.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        gdi32.SelectObject.restype = ctypes.c_void_p
        
        gdi32.DeleteObject.argtypes = [ctypes.c_void_p]
        gdi32.DeleteObject.restype = ctypes.c_bool
        
        gdi32.GetStockObject.argtypes = [ctypes.c_int]
        gdi32.GetStockObject.restype = ctypes.c_void_p
        
        gdi32.TextOutW.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_wchar_p, ctypes.c_int]
        gdi32.TextOutW.restype = ctypes.c_bool
        
        gdi32.SetTextColor.argtypes = [ctypes.c_void_p, ctypes.c_uint]
        gdi32.SetTextColor.restype = ctypes.c_uint
        
        gdi32.SetBkMode.argtypes = [ctypes.c_void_p, ctypes.c_int]
        gdi32.SetBkMode.restype = ctypes.c_int
        
        gdi32.SetTextAlign.argtypes = [ctypes.c_void_p, ctypes.c_uint]
        gdi32.SetTextAlign.restype = ctypes.c_uint
        
        gdi32.CreateFontW.argtypes = [
            ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
            ctypes.c_uint, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint,
            ctypes.c_uint, ctypes.c_uint, ctypes.c_uint, ctypes.c_wchar_p
        ]
        gdi32.CreateFontW.restype = ctypes.c_void_p
except ImportError:
    HAS_EMF_DEPENDENCY = False

class EMFInterceptDraw:
    """
    基于 ctypes.windll.gdi32 的 Windows EMF 绘图指令拦截代理。
    不需要第三方 pywin32 绑定依赖，即可实现矢量图元渲染。
    """
    def __init__(self, hdc, x0=0, y0=0, ssaa_factor=1, p=0):
        self.hdc = hdc
        self.x0 = x0
        self.y0 = y0
        self.sf = ssaa_factor
        self.p = p
        self.gdi = ctypes.windll.gdi32

    def _t_x(self, x):
        return int((x - self.x0) / self.sf + self.p)
        
    def _t_y(self, y):
        return int((y - self.y0) / self.sf + self.p)

    def _rgb_to_colorref(self, fill_str):
        """ Hex 颜色串 (#RRGGBB) 转 Windows COLORREF (0x00BBGGRR) """
        h = fill_str.lstrip('#')
        r, g, b = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
        return r | (g << 8) | (b << 16)

    def rectangle(self, xy, fill=None, outline=None, width=1, *args, **kwargs):
        x1, y1, x2, y2 = xy
        tx1, ty1, tx2, ty2 = self._t_x(x1), self._t_y(y1), self._t_x(x2), self._t_y(y2)
        
        # 1. 配置填充色画刷
        if fill:
            color = self._rgb_to_colorref(fill)
            brush = self.gdi.CreateSolidBrush(color)
            old_brush = self.gdi.SelectObject(self.hdc, brush)
        else:
            old_brush = self.gdi.SelectObject(self.hdc, self.gdi.GetStockObject(Config.GDI['null_brush']))
            
        # 2. 配置边框色画笔
        if outline:
            color = self._rgb_to_colorref(outline)
            pen_w = max(1, int(width / self.sf))
            pen = self.gdi.CreatePen(Config.GDI['ps_solid'], pen_w, color)
            old_pen = self.gdi.SelectObject(self.hdc, pen)
        else:
            old_pen = self.gdi.SelectObject(self.hdc, self.gdi.GetStockObject(Config.GDI['null_pen']))
            
        # 3. 图元绘制
        self.gdi.Rectangle(self.hdc, tx1, ty1, tx2, ty2)
        
        # 4. 回收清理
        if fill:
            self.gdi.DeleteObject(self.gdi.SelectObject(self.hdc, old_brush))
        if outline:
            self.gdi.DeleteObject(self.gdi.SelectObject(self.hdc, old_pen))

    def line(self, xy, fill="#374151", width=2, *args, **kwargs):
        if len(xy) < 2:
            return
            
        color = self._rgb_to_colorref(fill)
        pen_w = max(1, int(width / self.sf))
        pen = self.gdi.CreatePen(Config.GDI['ps_solid'], pen_w, color)
        old_pen = self.gdi.SelectObject(self.hdc, pen)
        
        # 1. 构造 POINT 结构体数组
        n_points = len(xy)
        point_array = (POINT * n_points)()
        for i, pt in enumerate(xy):
            point_array[i].x = self._t_x(pt[0])
            point_array[i].y = self._t_y(pt[1])
            
        # 2. 调用 GDI32 的 Polyline 进行连续折线绘制
        self.gdi.Polyline(self.hdc, ctypes.byref(point_array), n_points)
            
        self.gdi.DeleteObject(self.gdi.SelectObject(self.hdc, old_pen))

    def text(self, xy, text, fill="#000000", font=None, *args, **kwargs):
        x, y = xy
        tx, ty = self._t_x(x), self._t_y(y)
        color = self._rgb_to_colorref(fill)
        
        font_h = max(1, int((font.size if font else 22) / self.sf))
        # CreateFontW 参数使用配置中心定义的常量，以避免魔法数
        gdi_font = self.gdi.CreateFontW(
            -font_h, 0, 0, 0, Config.GDI['fw_normal'], 0, 0, 0,
            Config.GDI['default_charset'], 0, 0, Config.GDI['antialiased_quality'],
            0, Config.FONTS['gdi_family']
        )
        old_font = self.gdi.SelectObject(self.hdc, gdi_font)
        
        self.gdi.SetTextColor(self.hdc, color)
        self.gdi.SetBkMode(self.hdc, Config.GDI['bk_transparent'])
        
        # 使用 TA_CENTER | TA_BASELINE 对齐实现文本水平几何居中
        self.gdi.SetTextAlign(self.hdc, Config.GDI['ta_center_baseline'])
        # 配合基线对齐在垂直方向上做微调，以实现更好的居中效果
        ty_offset = ty + int(Config.GDI['baseline_offset_ratio'] * font_h)
        
        self.gdi.TextOutW(self.hdc, tx, ty_offset, text, len(text))
        
        self.gdi.DeleteObject(self.gdi.SelectObject(self.hdc, old_font))
