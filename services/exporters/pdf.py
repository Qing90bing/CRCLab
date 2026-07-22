import io
from services.exporters.base import BaseExporter
from services.exporters.svg import SVGExporter

# 动态延迟加载 PDF 系统底层渲染依赖
try:
    from svglib.svglib import svg2rlg
    from reportlab.graphics import renderPDF
    HAS_PDF_DEPENDENCY = True
except ImportError:
    HAS_PDF_DEPENDENCY = False

class PDFExporter(BaseExporter):
    """
    通过 XML 矢量网关转换为 ReportLab 的 PDF 物理写入及粗估插件。
    """
    @staticmethod
    def save(app, out_path, show_border, color_mode, **kwargs):
        """
        核心物理保存：将拦截并渲染的 SVG 代码转换为 ReportLab 绘图节点并输出为 PDF 文件。
        """
        if not HAS_PDF_DEPENDENCY:
            raise ImportError("未检测到 PDF 矢量导出依赖！请先在命令行运行 pip install svglib reportlab 导入支持。")
            
        data = app.data_var.get().strip()
        divisor = app.divisor_var.get().strip()
        q, rows, dividend = app.calculate_current(data, divisor)
        
        ctx = app._get_render_context()
        ctx['view_scale'] = 1.0
        ctx['show_border'] = show_border
        ctx['color_mode'] = color_mode
        
        # 1. 先行渲染生成标准的 SVG XML 字符串
        svg_content, _, _ = SVGExporter.render_to_svg(app.renderer, data, dividend, divisor, q, rows, ctx)
        
        # 2. 将 SVG 流读入 Reportlab 进行矢量转换并保存成文件
        svg_io = io.BytesIO(svg_content.encode("utf-8"))
        drawing = svg2rlg(svg_io)
        renderPDF.drawToFile(drawing, out_path)

    @staticmethod
    def estimate_size(app, data, dividend, divisor, q, rows, ctx, color_mode, show_border, **kwargs):
        """
        在后台内存中模拟完整的 SVG 到 PDF 的流转及矢量序列化，获取 PDF 的精准物理大小。
        """
        if not HAS_PDF_DEPENDENCY:
            return 0, 0, 0
        try:
            pdf_ctx = ctx.copy()
            pdf_ctx['color_mode'] = color_mode
            pdf_ctx['show_border'] = show_border
            
            # 1. 渲染生成临时 SVG 代码
            svg_content, w, h = SVGExporter.render_to_svg(app.renderer, data, dividend, divisor, q, rows, pdf_ctx)
            
            # 2. 将流注入 Reportlab 的 PDF 物理流包装器
            svg_io = io.BytesIO(svg_content.encode("utf-8"))
            drawing = svg2rlg(svg_io)
            
            pdf_bio = io.BytesIO()
            renderPDF.drawToFile(drawing, pdf_bio)
            
            # 3. 测量字节流长度并格式化
            size_bytes = len(pdf_bio.getvalue())
            return size_bytes, w, h
        except Exception:
            return 0, 0, 0
