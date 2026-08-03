from config.constants import Config
from core.engine import CRCEngine
from view.components.renderer import CanvasRenderer

BLOCK = (226, 232, 240)  # #e2e8f0
VALID_GREEN = (22, 163, 74)
INVALID_RED = (220, 38, 38)


def make_ctx(**overrides):
    ctx = {
        "view_scale": 1.0,
        "is_verify": False,
        "font_size": 38,
        "grid_base": Config.GRID_BASE,
        "h_spacing": 1.2,
        "v_spacing": 1.4,
        "line_width": 2,
        "padding": 30,
        "show_border": True,
        "is_preview": True,
        "ext_left": 0,
        "ext_right": 0,
        "curve_span_left": -0.5,
        "curve_span_right": 0.0,
        "bold_zeros": False,
        "bold_divisor": False,
        "bold_quotient": False,
        "bold_dividend": False,
        **Config.DEFAULT_COLORS,
    }
    ctx.update(overrides)
    return ctx


def _render(mode, frame, divisor="1011", **ctx_overrides):
    renderer = CanvasRenderer(None)
    if mode == "encode":
        q, rows, dividend = CRCEngine.calculate(frame, divisor)
    else:
        q, rows, dividend, _, _ = CRCEngine.verify(frame, divisor)
    ctx = make_ctx(is_verify=(mode == "verify"), **ctx_overrides)
    return renderer.render(frame, dividend, divisor, q, rows, ctx)


def _count_color(img, target):
    rgb = img.convert("RGB")
    w, h = rgb.size
    return sum(1 for y in range(0, h, 2) for x in range(0, w, 2) if rgb.getpixel((x, y))[:3] == target)


def test_encode_has_padding_block():
    img = _render("encode", "110101")
    assert _count_color(img, BLOCK) > 0


def test_verify_valid_has_no_block():
    img = _render("verify", "110101111")  # valid frame
    assert _count_color(img, BLOCK) == 0


def test_verify_invalid_has_error_block():
    img = _render("verify", "110101110")  # flipped last bit
    assert _count_color(img, BLOCK) > 0


def test_canvas_never_uses_red_or_green():
    img = _render("verify", "110101110")
    assert _count_color(img, VALID_GREEN) == 0
    assert _count_color(img, INVALID_RED) == 0
