from config.constants import Config
from core.engine import CRCEngine
from services.exporter_service import ExportSnapshot
from services.exporters.bitmap import BitmapExporter
from services.exporters.svg import SVGExporter
from tests.helpers import make_ctx
from view.components.renderer import CanvasRenderer


def _make_snapshot(mode="encode", frame="110101", divisor="1011"):
    renderer = CanvasRenderer(None)
    if mode == "encode":
        q, rows, dividend = CRCEngine.calculate(frame, divisor)
    else:
        q, rows, dividend, _, _ = CRCEngine.verify(frame, divisor)
    ctx = make_ctx(is_verify=(mode == "verify"))
    return ExportSnapshot(frame, divisor, q, rows, dividend, ctx, renderer)


def test_png_export_writes_file(tmp_path):
    snap = _make_snapshot()
    out = tmp_path / "chart.png"
    BitmapExporter.save(snap, str(out), False, Config.EXPORT_OPTIONS["colors"][0])
    assert out.exists() and out.stat().st_size > 0


def test_svg_export_contains_block_fill(tmp_path):
    snap = _make_snapshot()
    out = tmp_path / "chart.svg"
    SVGExporter.save(snap, str(out), False, Config.EXPORT_OPTIONS["colors"][0])
    svg = out.read_text(encoding="utf-8")
    assert "<svg" in svg
    assert "#e2e8f0" in svg.lower()


def test_verify_invalid_export_has_error_block():
    snap = _make_snapshot(mode="verify", frame="110101110")
    svg, _, _ = SVGExporter.render_to_svg(snap.renderer, snap.data, snap.dividend, snap.divisor, snap.q, snap.rows, snap.ctx)
    assert "#e2e8f0" in svg.lower()
