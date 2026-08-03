from config.constants import Config


def parse_color(color_in):
    """
    通用颜色解析工具：兼容 #RGB / #RRGGBB / #RRGGBBAA 与常见颜色名，返回 (r, g, b, a)。
    各导出器共用，避免多处重复实现。
    """
    if not color_in:
        return (0, 0, 0, 255)
    if isinstance(color_in, tuple):
        if len(color_in) == 3:
            return (color_in[0], color_in[1], color_in[2], 255)
        elif len(color_in) == 4:
            return color_in
    c_str = str(color_in).strip()
    if c_str.startswith("#"):
        h = c_str.lstrip("#")
        if len(h) == 3:
            h = "".join(x + x for x in h)
        if len(h) in (6, 8):
            try:
                if len(h) == 6:
                    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)
                return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), int(h[6:8], 16))
            except ValueError:
                # 非法 hex 颜色，回退为黑色
                return (0, 0, 0, 255)
    color_map = {
        "white": (255, 255, 255, 255),
        "black": (0, 0, 0, 255),
        "none": (0, 0, 0, 0),
    }
    return color_map.get(c_str.lower(), (0, 0, 0, 255))


def apply_color_mode(r, g, b, color_mode):
    """
    统一灰度 / 黑白 色彩过滤，避免各导出器重复实现。
    返回过滤后的 (r, g, b)。
    """
    if color_mode == Config.EXPORT_OPTIONS['colors'][1]:
        y = int(0.299 * r + 0.587 * g + 0.114 * b)
        return y, y, y
    elif color_mode == Config.EXPORT_OPTIONS['colors'][2]:
        y = int(0.299 * r + 0.587 * g + 0.114 * b)
        v = 255 if y >= 127 else 0
        return v, v, v
    return r, g, b
