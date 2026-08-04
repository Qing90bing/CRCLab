from pathlib import Path

import pytest

from config import paths
from config.constants import Config
from core.engine import CRCEngine
from services.exporter_service import Exporter, ExportSnapshot
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


def test_default_export_does_not_depend_on_current_directory(tmp_path, monkeypatch):
    snap = _make_snapshot()
    app_dir = tmp_path / "app"
    work_dir = tmp_path / "work"
    work_dir.mkdir()
    monkeypatch.setattr(paths, "default_export_dir", lambda: app_dir)
    monkeypatch.chdir(work_dir)

    out_path, export_dir, _, _ = Exporter.export(
        snap,
        "chart",
        "png",
        False,
        Config.EXPORT_OPTIONS["colors"][0],
        Config.EXPORT_OPTIONS["qualities"][0],
        80,
        300,
        Config.EXPORT_OPTIONS["dir_modes"][0],
        "",
    )

    assert Path(out_path).parent == app_dir
    assert Path(export_dir) == app_dir
    assert Path(out_path).is_file()


def test_export_rejects_path_traversal_filename(tmp_path):
    snap = _make_snapshot()

    with pytest.raises(ValueError):
        Exporter.export(
            snap,
            "..\\chart",
            "png",
            False,
            Config.EXPORT_OPTIONS["colors"][0],
            Config.EXPORT_OPTIONS["qualities"][0],
            80,
            300,
            Config.EXPORT_OPTIONS["dir_modes"][0],
            "",
        )


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
