import platform
import ctypes
from PIL import Image, ImageDraw
from config.constants import Config
from view.exporters.base import BaseExporter

# 动态加载 Windows 底层 GDI32 矢量依赖
try:
    HAS_EMF_DEPENDENCY = (platform.system() == "Windows")
    if HAS_EMF_DEPENDENCY:
        class POINT(ctypes.Structure):
            _fields_ = [("x", ctypes.c_int), ("y", ctypes.c_int)]
            
        gdi32 = ctypes.windll.gdi32
        
        # 声明 GDI32 类型安全 C 接口函数参数
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
except Exception:
    HAS_EMF_DEPENDENCY = False


class EMFInterceptDraw:
    """
    基于 ctypes.windll.gdi32 的 Windows EMF 绘图指令拦截代理。
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
        if fill in ("transparent", "none"):
            fill = None
        if outline in ("transparent", "none"):
            outline = None
        x1, y1, x2, y2 = xy
        tx1, ty1, tx2, ty2 = self._t_x(x1), self._t_y(y1), self._t_x(x2), self._t_y(y2)
        
        if fill:
            color = self._rgb_to_colorref(fill)
            brush = self.gdi.CreateSolidBrush(color)
            old_brush = self.gdi.SelectObject(self.hdc, brush)
        else:
            old_brush = self.gdi.SelectObject(self.hdc, self.gdi.GetStockObject(Config.GDI['null_brush']))
            
        if outline:
            color = self._rgb_to_colorref(outline)
            pen_w = max(1, int(width / self.sf))
            pen = self.gdi.CreatePen(Config.GDI['ps_solid'], pen_w, color)
            old_pen = self.gdi.SelectObject(self.hdc, pen)
        else:
            old_pen = self.gdi.SelectObject(self.hdc, self.gdi.GetStockObject(Config.GDI['null_pen']))
            
        self.gdi.Rectangle(self.hdc, tx1, ty1, tx2, ty2)
        
        if fill:
            self.gdi.DeleteObject(self.gdi.SelectObject(self.hdc, old_brush))
        if outline:
            self.gdi.DeleteObject(self.gdi.SelectObject(self.hdc, old_pen))

    def line(self, xy, fill="#374151", width=2, *args, **kwargs):
        if fill in ("transparent", "none"):
            return
        if len(xy) < 2:
            return
            
        color = self._rgb_to_colorref(fill)
        pen_w = max(1, int(width / self.sf))
        pen = self.gdi.CreatePen(Config.GDI['ps_solid'], pen_w, color)
        old_pen = self.gdi.SelectObject(self.hdc, pen)
        
        n_points = len(xy)
        point_array = (POINT * n_points)()
        for i, pt in enumerate(xy):
            point_array[i].x = self._t_x(pt[0])
            point_array[i].y = self._t_y(pt[1])
            
        self.gdi.Polyline(self.hdc, ctypes.byref(point_array), n_points)
        self.gdi.DeleteObject(self.gdi.SelectObject(self.hdc, old_pen))

    def text(self, xy, text, fill="#000000", font=None, *args, **kwargs):
        if fill in ("transparent", "none"):
            return
        x, y = xy
        tx, ty = self._t_x(x), self._t_y(y)
        color = self._rgb_to_colorref(fill)
        
        font_h = max(1, int((font.size if font else 22) / self.sf))
        gdi_font = self.gdi.CreateFontW(
            -font_h, 0, 0, 0, Config.GDI['fw_normal'], 0, 0, 0,
            Config.GDI['default_charset'], 0, 0, Config.GDI['antialiased_quality'],
            0, Config.FONTS['gdi_family']
        )
        old_font = self.gdi.SelectObject(self.hdc, gdi_font)
        
        self.gdi.SetTextColor(self.hdc, color)
        self.gdi.SetBkMode(self.hdc, Config.GDI['bk_transparent'])
        
        self.gdi.SetTextAlign(self.hdc, Config.GDI['ta_center_baseline'])
        ty_offset = ty + int(Config.GDI['baseline_offset_ratio'] * font_h)
        
        self.gdi.TextOutW(self.hdc, tx, ty_offset, text, len(text))
        self.gdi.DeleteObject(self.gdi.SelectObject(self.hdc, old_font))


class EMFExporter(BaseExporter):
    """
    Windows GDI32 矢量增强型图元 (EMF) 原生写盘与估算插件。
    """
    @staticmethod
    def save(app, out_path, show_border, color_mode, **kwargs):
        """
        核心物理保存：启动 Windows 原生 GDI 拦截器，物理渲染矢量 EMF 图元到物理文件。
        """
        if not HAS_EMF_DEPENDENCY:
            raise NotImplementedError("EMF 矢量导出格式仅支持在 Windows 操作系统下运行。")
            
        data = app.data_var.get().strip()
        divisor = app.divisor_var.get().strip()
        q, rows, dividend = app.engine.calculate(data, divisor)
        
        ctx = app._get_render_context()
        ctx['view_scale'] = 1.0
        ctx['show_border'] = show_border
        ctx['color_mode'] = color_mode
        
        path_ptr = ctypes.c_wchar_p(out_path)
        hdc = ctypes.windll.gdi32.CreateEnhMetaFileW(0, path_ptr, None, "CRCLab Chart")
        if not hdc:
            raise OSError("无法创建 EMF 设备上下文。")
            
        try:
            EMFExporter.draw_to_emf(app, hdc, data, dividend, divisor, q, rows, ctx)
        finally:
            hemf = ctypes.windll.gdi32.CloseEnhMetaFile(hdc)
            if hemf:
                ctypes.windll.gdi32.DeleteEnhMetaFile(hemf)

    @staticmethod
    def estimate_size(app, data, dividend, divisor, q, rows, ctx, color_mode, show_border, **kwargs):
        """
        使用 Windows GDI 原生接口创建虚拟内存 EMF 设备，并精确计算其产生的底层二进制字节流大小。
        """
        if not HAS_EMF_DEPENDENCY:
            return "EMF仅限Windows系统"
        try:
            hdc = ctypes.windll.gdi32.CreateEnhMetaFileW(0, None, None, "CRCLab Chart")
            if not hdc:
                return "估算失败"
                
            EMFExporter.draw_to_emf(app, hdc, data, dividend, divisor, q, rows, ctx)
            hemf = ctypes.windll.gdi32.CloseEnhMetaFile(hdc)
            if not hemf:
                return "估算失败"
                
            size = ctypes.windll.gdi32.GetEnhMetaFileBits(hemf, 0, None)
            if size > 0:
                buf = ctypes.create_string_buffer(size)
                ctypes.windll.gdi32.GetEnhMetaFileBits(hemf, size, buf)
                size_kb = len(buf.raw) / 1024.0
                size_text = f"{size_kb:.2f} KB"
            else:
                size_text = "估算失败"
            ctypes.windll.gdi32.DeleteEnhMetaFile(hemf)
            return size_text
        except Exception:
            return "估算失败"

    @staticmethod
    def draw_to_emf(app, hdc, data, dividend, divisor, q, rows, ctx):
        """
        核心物理转换：计算坐标原点安全偏置并触发代理将 CanvasRenderer 命令分发 to GDI。
        """
        ssaa_factor = Config.LAYOUT['ssaa_factor']
        ctx_ssaa = ctx.copy()
        ctx_ssaa['view_scale'] = ctx['view_scale'] * ssaa_factor

        # 1. 物理计算与拦截器初始化，用于获取裁剪用 bounding box
        renderer = app.renderer
        L = renderer._calculate_layout(ctx_ssaa, dividend, divisor)
        ox, oy, w_temp, h_temp = renderer._estimate_bounds(ctx_ssaa, L, rows)
        
        bbox = EMFExporter._calc_temp_bbox(renderer, data, q, dividend, divisor, rows, ctx_ssaa, L, ox, oy, w_temp, h_temp)
        if not bbox:
            return
            
        x0, y0, x1, y1 = bbox
        p = int(ctx['padding'] * ctx['view_scale'])
        
        # 2. 调用 GDI 拦截器进行矢量图元物理绘制
        draw_proxy = EMFInterceptDraw(hdc, x0, y0, ssaa_factor, p)
        EMFExporter._draw_emf_elements(renderer, draw_proxy, data, q, dividend, divisor, rows, ctx_ssaa, L, ox, oy, x0, y0, x1, y1, p, ssaa_factor)

    @staticmethod
    def _calc_temp_bbox(renderer, data, q, dividend, divisor, rows, ctx_ssaa, L, ox, oy, w_temp, h_temp):
        """ 在超采样的临时画布上绘制公式并获取其 getbbox 坐标 """
        img_temp = Image.new("RGBA", (w_temp, h_temp), (0, 0, 0, 0))
        draw_real = ImageDraw.Draw(img_temp)
        
        renderer._draw_quotient(draw_real, q, L, ctx_ssaa, ox, oy)
        line_y = renderer._draw_header_elements(draw_real, dividend, L, ctx_ssaa, ox, oy)
        renderer._draw_operands(draw_real, data, dividend, divisor, line_y, L, ctx_ssaa, ox, oy)
        renderer._draw_steps(draw_real, rows, data, line_y, L, ctx_ssaa, ox, oy)
        
        return img_temp.getbbox()

    @staticmethod
    def _draw_emf_elements(renderer, draw_proxy, data, q, dividend, divisor, rows, ctx_ssaa, L, ox, oy, x0, y0, x1, y1, p, ssaa_factor):
        """ 利用拦截器执行具体 GDI 指令输出 """
        # 绘制背景底板（若为透明底则跳过绘制）
        sheet_bg_color = ctx_ssaa.get('sheet_bg_color', '#ffffff')
        if sheet_bg_color not in ("transparent", "none"):
            draw_proxy.rectangle(
                [x0 - p * ssaa_factor, y0 - p * ssaa_factor, x1 + p * ssaa_factor, y1 + p * ssaa_factor],
                fill=sheet_bg_color,
                outline=None
            )
        
        # 绘制长除法各图元部分
        renderer._draw_quotient(draw_proxy, q, L, ctx_ssaa, ox, oy)
        line_y = renderer._draw_header_elements(draw_proxy, dividend, L, ctx_ssaa, ox, oy)
        renderer._draw_operands(draw_proxy, data, dividend, divisor, line_y, L, ctx_ssaa, ox, oy)
        renderer._draw_steps(draw_proxy, rows, data, line_y, L, ctx_ssaa, ox, oy)

        # 绘制外边框线
        if ctx_ssaa.get('show_border', True):
            border_w = max(1.0, 2.0 * (ctx_ssaa['view_scale'] / ssaa_factor))
            draw_proxy.rectangle(
                [x0 - p * ssaa_factor, y0 - p * ssaa_factor, x1 + p * ssaa_factor, y1 + p * ssaa_factor],
                fill=None,
                outline="#000000",
                width=border_w * ssaa_factor
            )
