import os
from contextlib import suppress

from config.constants import Config
from services.exporters import EXPORTERS


class ExportSnapshot:
    """
    主线程采集的导出数据快照，避免后台导出线程跨线程读取 Tk 变量（Tkinter 非线程安全）。
    包含导出所需的全部数据与渲染上下文，工作线程仅消费快照。
    """

    __slots__ = ("ctx", "data", "dividend", "divisor", "q", "renderer", "rows")

    def __init__(self, data, divisor, q, rows, dividend, ctx, renderer):
        self.data = data
        self.divisor = divisor
        self.q = q
        self.rows = rows
        self.dividend = dividend
        self.ctx = ctx
        self.renderer = renderer


class Exporter:
    """
    高阶导出协调外观类 (Facade)。

    统一面向 GUI 交互控制器，提供完全稳定的外层 API，
    底层则根据格式动态分发给对应的子导出器插件（工厂模式）执行物理写盘与体积估算。
    这样即使以后增加格式，此外部协调器及 UI 控制层也能保持 100% 稳定，符合开闭原则（OCP）。
    """

    @staticmethod
    def export(snap, filename, fmt, show_border, color_mode, quality_name, jpg_quality, dpi_val, dir_mode, custom_dir):
        """
        统一物理导出入口。通过工厂映射字典分发至具体物理插件。
        """
        opt_q = Config.EXPORT_OPTIONS["qualities"]
        multiplier = {opt_q[0]: 1, opt_q[1]: 2, opt_q[2]: 3, opt_q[3]: 4}[quality_name]

        # 1. 物理导出结果存储目录初始化
        if dir_mode == Config.EXPORT_OPTIONS["dir_modes"][0]:
            export_dir = os.path.join(os.getcwd(), "导出结果")
            os.makedirs(export_dir, exist_ok=True)
        else:
            export_dir = custom_dir
            if not export_dir:
                raise ValueError(Config.MESSAGES["warning_custom_dir_empty"])
            if not os.path.exists(export_dir) or not os.path.isdir(export_dir):
                raise FileNotFoundError(f"指定的自定义导出目录不存在或无效：{export_dir}")

        # 自动重命名，防止覆盖已有文件
        base_name = filename
        out_path = os.path.join(export_dir, f"{base_name}.{fmt}")
        counter = 1
        while os.path.exists(out_path):
            out_path = os.path.join(export_dir, f"{base_name}_{counter}.{fmt}")
            counter += 1

        # 2. 动态查找注册的格式插件并调用执行
        exporter_cls = EXPORTERS.get(fmt.lower())
        if not exporter_cls:
            raise NotImplementedError(f"未注册的导出格式：{fmt}")

        exporter_cls.save(snap, out_path, show_border, color_mode, multiplier=multiplier, dpi_val=dpi_val, jpg_quality=jpg_quality)

        # 获取导出的物理像素尺寸
        width, height = 0, 0
        if fmt.lower() in ("png", "jpg", "jpeg"):
            try:
                from PIL import Image

                with Image.open(out_path) as img:
                    width, height = img.size
            except Exception:
                pass
        else:
            with suppress(Exception):
                _, width, height = exporter_cls.estimate_size(
                    snap, snap.data, snap.dividend, snap.divisor, snap.q, snap.rows, snap.ctx, color_mode, show_border, fmt=fmt
                )

        return out_path, export_dir, width, height

    @staticmethod
    def estimate_vector_size(app, fmt, data, dividend, divisor, q, rows, ctx, color_mode, show_border):
        """
        测算并返回矢量格式 (SVG, PDF, EMF) 导出的预估文件大小及精确宽高长宽。
        """
        exporter_cls = EXPORTERS.get(fmt.lower())
        if not exporter_cls:
            return "估算失败", 0, 0
        return exporter_cls.estimate_size(app, data, dividend, divisor, q, rows, ctx, color_mode, show_border, fmt=fmt)

    @staticmethod
    def calculate_precise_bitmap_size(
        app, data, dividend, divisor, q, rows, ctx, color_mode, show_border, multiplier, save_fmt, dpi_val, jpg_quality=80
    ):
        """
        高分辨率位图在后台模拟物理重绘并精密评估大小和真实宽高 (返回元组 (size_bytes, w, h))。
        """
        exporter_cls = EXPORTERS.get("png") if save_fmt.lower() not in EXPORTERS else EXPORTERS.get(save_fmt.lower())
        if not exporter_cls:
            return 0, 0, 0

        return exporter_cls.estimate_size(
            app,
            data,
            dividend,
            divisor,
            q,
            rows,
            ctx,
            color_mode,
            show_border,
            multiplier=multiplier,
            dpi_val=dpi_val,
            fmt=save_fmt,
            jpg_quality=jpg_quality,
        )
