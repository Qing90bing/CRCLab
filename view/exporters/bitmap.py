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
        dpi_scale = dpi_val / 96.0
        
        data = app.data_var.get().strip()
        divisor = app.divisor_var.get().strip()
        q, rows, dividend = app.engine.calculate(data, divisor)
        
        ctx = app._get_render_context()
        ctx['view_scale'] = 1.0 * multiplier * dpi_scale
        ctx['show_border'] = show_border
        ctx['is_preview'] = False
        
        # 1. 委托渲染器生成基础 Pillow 图像
        img = app.renderer.render(data, dividend, divisor, q, rows, ctx)
        save_fmt = "JPEG" if out_path.lower().endswith((".jpg", ".jpeg")) else "PNG"
        img = BitmapExporter._apply_color_mode(img, color_mode, save_fmt)
            
        img.save(out_path, format=save_fmt, dpi=(dpi_val, dpi_val))

    @staticmethod
    def estimate_size(app, data, dividend, divisor, q, rows, ctx, color_mode, show_border, **kwargs):
        """
        高精度物理重绘估算，直接采用真实目标分辨率进行内存仿真渲染，实现 100% 完美的预估文件大小。
        """
        multiplier = kwargs.get('multiplier', 1)
        dpi_val = kwargs.get('dpi_val', 96)
        dpi_scale = dpi_val / 96.0
        fmt = kwargs.get('fmt', 'png')
        
        # 1. 直接以目标倍率渲染真实的图像
        ctx_real = ctx.copy()
        ctx_real['view_scale'] = 1.0 * multiplier * dpi_scale
        ctx_real['show_border'] = show_border
        ctx_real['is_preview'] = False
        
        img_real = app.renderer.render(data, dividend, divisor, q, rows, ctx_real)
        save_fmt = "JPEG" if fmt.lower() in ("jpg", "jpeg") else "PNG"
        img_real = BitmapExporter._apply_color_mode(img_real, color_mode, save_fmt)
        
        # 2. 模拟真实保存的二进制写入，获取 100% 精确的物理字节大小
        bio = io.BytesIO()
        img_real.save(bio, format=save_fmt, dpi=(dpi_val, dpi_val))
        size_bytes = len(bio.getvalue())
        
        return size_bytes, img_real.width, img_real.height

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
                return img.convert("L").point(lambda x: 0 if x < 128 else 255, 'L').convert("1")
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
                rgb_gray = Image.merge("RGB", (r, g, b)).convert("L")
                rgb_bw = rgb_gray.point(lambda x: 0 if x < 128 else 255, 'L')
                return Image.merge("RGBA", (rgb_bw, rgb_bw, rgb_bw, a))
            return img.convert("L").point(lambda x: 0 if x < 128 else 255, 'L').convert("1")
            
        # 3. PNG 彩色模式保留完整的 RGBA，支持真正的透明背景
        return img
