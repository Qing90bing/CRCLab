import os
from config.constants import Config
from view.exporters import EXPORTERS

class Exporter:
    """
    高阶导出协调外观类 (Facade)。
    
    统一面向 GUI 交互控制器，提供完全稳定的外层 API，
    底层则根据格式动态分发给对应的子导出器插件（工厂模式）执行物理写盘与体积估算。
    这样即使以后增加格式，此外部协调器及 UI 控制层也能保持 100% 稳定，符合开闭原则（OCP）。
    """
    @staticmethod
    def export(app, fmt, show_border, color_mode, quality_name, dpi_val, dir_mode, custom_dir):
        """
        统一物理导出入口。通过工厂映射字典分发至具体物理插件。
        """
        opt_q = Config.EXPORT_OPTIONS['qualities']
        multiplier = {
            opt_q[0]: 1, opt_q[1]: 1, opt_q[2]: 2,
            opt_q[3]: 3, opt_q[4]: 4, opt_q[5]: 6
        }[quality_name]

        # 1. 物理导出结果存储目录初始化
        if dir_mode == Config.EXPORT_OPTIONS['dir_modes'][0]:
            export_dir = os.path.join(os.getcwd(), "导出结果")
        else:
            export_dir = custom_dir

        if not export_dir:
            raise ValueError(Config.MESSAGES['warning_custom_dir_empty'])
        os.makedirs(export_dir, exist_ok=True)
        
        out_path = os.path.join(export_dir, f"crc_export.{fmt}")

        # 2. 动态查找注册的格式插件并调用执行
        exporter_cls = EXPORTERS.get(fmt.lower())
        if not exporter_cls:
            raise NotImplementedError(f"未注册的导出格式：{fmt}")
            
        exporter_cls.save(
            app, out_path, show_border, color_mode,
            multiplier=multiplier, dpi_val=dpi_val
        )
        return out_path, export_dir

    @staticmethod
    def estimate_vector_size(app, fmt, data, dividend, divisor, q, rows, ctx, color_mode, show_border):
        """
        测算并返回矢量格式 (SVG, PDF, EMF) 导出的预估文件大小 (格式化为字符串，如 "12.45 KB")。
        """
        exporter_cls = EXPORTERS.get(fmt.lower())
        if not exporter_cls:
            return "估算失败"
        return exporter_cls.estimate_size(
            app, data, dividend, divisor, q, rows, ctx, color_mode, show_border,
            fmt=fmt
        )

    @staticmethod
    def calculate_precise_bitmap_size(app, data, dividend, divisor, q, rows, ctx, color_mode, show_border, multiplier, save_fmt, dpi_val):
        """
        高分辨率位图在后台模拟物理重绘并精密评估大小 (返回浮点数 KB，以对接防抖刷新接口)。
        """
        exporter_cls = EXPORTERS.get("png") if save_fmt.lower() not in EXPORTERS else EXPORTERS.get(save_fmt.lower())
        if not exporter_cls:
            return 0.0
            
        size_str = exporter_cls.estimate_size(
            app, data, dividend, divisor, q, rows, ctx, color_mode, show_border,
            multiplier=multiplier, dpi_val=dpi_val, fmt=save_fmt
        )
        try:
            return float(size_str.replace("KB", "").strip())
        except Exception:
            return 0.0
