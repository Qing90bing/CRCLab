from config.constants import Config
from services.exporters.color_utils import apply_color_mode, parse_color


def test_parse_color_variants():
    assert parse_color("#fff") == (255, 255, 255, 255)
    assert parse_color("#ffffff") == (255, 255, 255, 255)
    assert parse_color("#fff8f8f8") == (255, 248, 248, 248)
    assert parse_color("black") == (0, 0, 0, 255)
    assert parse_color("none") == (0, 0, 0, 0)
    assert parse_color(None) == (0, 0, 0, 255)


def test_parse_color_invalid_hex_falls_back_to_black():
    assert parse_color("#xyz") == (0, 0, 0, 255)


def test_apply_color_mode():
    colors = Config.EXPORT_OPTIONS["colors"]
    gray = apply_color_mode(226, 232, 240, colors[1])
    assert gray[0] == gray[1] == gray[2]
    bw = apply_color_mode(226, 232, 240, colors[2])
    assert bw == (255, 255, 255)
    color = apply_color_mode(226, 232, 240, colors[0])
    assert color == (226, 232, 240)
