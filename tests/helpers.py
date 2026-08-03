from config.constants import Config


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
