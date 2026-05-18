import io
from PIL import Image
from config.constants import Config
from view.exporters.base import BaseExporter

class BitmapExporter(BaseExporter):
    """
    高分超采样位图 (PNG, JPEG) 导出及精算估计插件。
    """
    @staticmethod
    def save(app, out_path, show_border, color_mode, **kwargs):
        """
        以高分辨率超采样渲染位图图表并存盘。
        """
        multiplier = kwargs.get('multiplier', 1)
        dpi_val = kwargs.get('dpi_val', 96)
        
        data = app.data_var.get().strip()
        divisor = app.divisor_var.get().strip()
        q, rows, dividend = app.engine.calculate(data, divisor)
        
        ctx = app._get_render_context()
        ctx['view_scale'] = 1.0 * multiplier
        ctx['show_border'] = show_border
        ctx['is_preview'] = False
        
        # 1. 委托渲染器生成基础 Pillow 图像
        img = app.renderer.render(data, dividend, divisor, q, rows, ctx)
        save_fmt = "JPEG" if out_path.endswith(".jpg") else "PNG"
        img = BitmapExporter._apply_color_mode(img, color_mode, save_fmt)
            
        img.save(out_path, format=save_fmt, dpi=(dpi_val, dpi_val))

    @staticmethod
    def estimate_size(app, data, dividend, divisor, q, rows, ctx, color_mode, show_border, **kwargs):
        """
        在后台内存中模拟物理渲染与流写入，以极高精确度精算预估位图格式的文件字节数。
        """
        multiplier = kwargs.get('multiplier', 1)
        dpi_val = kwargs.get('dpi_val', 96)
        fmt = kwargs.get('fmt', 'png')
        
        ctx_calc = ctx.copy()
        ctx_calc['view_scale'] = 1.0 * multiplier
        ctx_calc['show_border'] = show_border
        ctx_calc['is_preview'] = False
        
        # 1. 精密绘制高分辨率内存公式
        img_calc = app.renderer.render(data, dividend, divisor, q, rows, ctx_calc)
        save_fmt = "JPEG" if fmt == "jpg" else "PNG"
        img_calc = BitmapExporter._apply_color_mode(img_calc, color_mode, save_fmt)
            
        # 2. 模拟二进制写入内存流，从而精准获取压缩编码后的物理字节大小
        bio_precise = io.BytesIO()
        img_calc.save(bio_precise, format=save_fmt, dpi=(dpi_val, dpi_val))
        
        size_kb = len(bio_precise.getvalue()) / 1024.0
        return f"{size_kb:.1f} KB"

    @staticmethod
    def _apply_color_mode(img, color_mode, save_fmt):
        """
        针对 Pillow 图像应用指定的色彩变调和滤镜效果，输出匹配颜色模式的画布。
        """
        save_fmt = save_fmt.upper()
        
        # 1. 针对不支持透明通道的 JPEG，在执行转换前若图像包含透明通道，应该先用白色底色合并
        if save_fmt == "JPEG":
            if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                background = Image.new("RGBA", img.size, (255, 255, 255, 255))
                background.paste(img, (0, 0), img)
                img = background
                
            if color_mode == Config.EXPORT_OPTIONS['colors'][1]:
                return img.convert("L")
            elif color_mode == Config.EXPORT_OPTIONS['colors'][2]:
                return img.convert("1")
            else:
                return img.convert("RGB")
                
        # 2. 针对支持透明通道的 PNG 格式，在灰度或黑白模式下，使用 split-and-merge 通道拆分合并，实现无损保留透明度
        if color_mode == Config.EXPORT_OPTIONS['colors'][1]:
            # 灰度模式，无损保留透明通道
            if img.mode in ("RGBA", "LA"):
                r, g, b, a = img.split()
                rgb_gray = Image.merge("RGB", (r, g, b)).convert("L")
                return Image.merge("RGBA", (rgb_gray, rgb_gray, rgb_gray, a))
            return img.convert("L")
            
        elif color_mode == Config.EXPORT_OPTIONS['colors'][2]:
            # 黑白模式，无损保留透明通道
            if img.mode in ("RGBA", "LA"):
                r, g, b, a = img.split()
                rgb_bw = Image.merge("RGB", (r, g, b)).convert("1").convert("L")
                return Image.merge("RGBA", (rgb_bw, rgb_bw, rgb_bw, a))
            return img.convert("1")
            
        # 3. PNG 彩色模式保留完整的 RGBA，支持真正的透明背景
        return img
