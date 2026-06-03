from services.exporters.bitmap import BitmapExporter
from services.exporters.svg import SVGExporter
from services.exporters.pdf import PDFExporter
from services.exporters.emf import EMFExporter

# 导出格式工厂注册清单。
# 后续若要支持新格式（例如 "html"），只需新建导出类并在此注册即可，外部零修改。
EXPORTERS = {
    "png": BitmapExporter,
    "jpg": BitmapExporter,
    "jpeg": BitmapExporter,
    "svg": SVGExporter,
    "pdf": PDFExporter,
    "emf": EMFExporter
}
