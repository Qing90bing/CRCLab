from PIL import Image, ImageDraw
from config.constants import Config

class SVGInterceptDraw:
    """
    轻量级绘图指令拦截器代理类。
    用于在内存绘制 Pillow 算式图像的同时，无感拦截记录所有 text, line, rectangle 原语。
    """
    def __init__(self, real_draw):
        self.real_draw = real_draw
        self.commands = []

    def text(self, xy, text, font=None, fill=None, anchor=None, *args, **kwargs):
        self.commands.append({
            'type': 'text',
            'xy': xy,
            'text': text,
            'font': font,
            'fill': fill,
            'anchor': anchor
        })
        return self.real_draw.text(xy, text, font=font, fill=fill, anchor=anchor, *args, **kwargs)

    def line(self, xy, fill=None, width=1, joint=None, *args, **kwargs):
        self.commands.append({
            'type': 'line',
            'xy': xy,
            'fill': fill,
            'width': width,
            'joint': joint
        })
        return self.real_draw.line(xy, fill=fill, width=width, joint=joint, *args, **kwargs)

    def rectangle(self, xy, fill=None, outline=None, width=1, *args, **kwargs):
        self.commands.append({
            'type': 'rectangle',
            'xy': xy,
            'fill': fill,
            'outline': outline,
            'width': width
        })
        return self.real_draw.rectangle(xy, fill=fill, outline=outline, width=width, *args, **kwargs)


class SVGRenderer:
    """
    SVG 矢量图专用渲染转换器。
    
    采用静态转换逻辑驱动传入的 CanvasRenderer 实质排版器，
    将拦截到的二维 Pillow 图形指令无损编译为标准的 SVG 1.1 矢量 XML 文本。
    """
    @staticmethod
    def render_to_svg(renderer, data, dividend, divisor, q, rows, ctx):
        """
        将 CRC 除法步骤绘制过程渲染并生成高品质无损 SVG 矢量字符串。
        完全复用 CanvasRenderer 实例的排版和绘制方法，从而保持与 Pillow 预览的像素级一致性。
        """
        ssaa_factor = Config.LAYOUT['ssaa_factor']
        ctx_ssaa = ctx.copy()
        ctx_ssaa['view_scale'] = ctx['view_scale'] * ssaa_factor

        # 1. 临时高分画布与拦截器初始化
        L = renderer._calculate_layout(ctx_ssaa, dividend, divisor)
        s = L['s']
        
        w_temp = int(Config.LAYOUT['temp_canvas_base'] * max(1.0, s))
        h_temp = int(Config.LAYOUT['temp_canvas_base'] * max(1.0, s))
        img_temp = Image.new("RGBA", (w_temp, h_temp), (0, 0, 0, 0))
        draw_real = ImageDraw.Draw(img_temp)
        draw_temp = SVGInterceptDraw(draw_real)
        
        ox = Config.LAYOUT['draw_origin_offset'] * s
        oy = Config.LAYOUT['draw_origin_offset'] * s
        
        # 2. 执行与 Pillow 实质渲染完全一致的几何绘制指令
        renderer._draw_quotient(draw_temp, q, L, ctx_ssaa, ox, oy)
        line_y = renderer._draw_header_elements(draw_temp, dividend, L, ctx_ssaa, ox, oy)
        renderer._draw_operands(draw_temp, data, dividend, divisor, line_y, L, ctx_ssaa, ox, oy)
        renderer._draw_steps(draw_temp, rows, data, line_y, L, ctx_ssaa, ox, oy)
        
        # 3. 获取公式的裁剪边界盒
        bbox = img_temp.getbbox()
        if not bbox:
            return ""
            
        x0, y0, x1, y1 = bbox
        
        # 4. 计算缩放及纸张尺寸
        p = int(ctx['padding'] * ctx['view_scale'])
        w_sheet = int((x1 - x0) / ssaa_factor) + 2 * p
        h_sheet = int((y1 - y0) / ssaa_factor) + 2 * p
        
        # Helper: 解析全格式颜色，统一输出 (R, G, B, A) 元组
        def parse_color(color_in):
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
                if len(h) == 6:
                    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)
                elif len(h) == 8:
                    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), int(h[6:8], 16))
            elif c_str.startswith("rgb("):
                parts = c_str.replace("rgb(", "").replace(")", "").split(",")
                return (int(parts[0]), int(parts[1]), int(parts[2]), 255)
            elif c_str.startswith("rgba("):
                parts = c_str.replace("rgba(", "").replace(")", "").split(",")
                return (int(parts[0]), int(parts[1]), int(parts[2]), int(float(parts[3]) * 255))
            
            color_map = {
                "white": (255, 255, 255, 255),
                "black": (0, 0, 0, 255),
                "none": (0, 0, 0, 0)
            }
            return color_map.get(c_str.lower(), (0, 0, 0, 255))

        # Helper: 转换并应用灰度/黑白滤镜，输出兼容的 SVG 色彩串
        color_mode = ctx.get('color_mode', Config.EXPORT_OPTIONS['colors'][0])
        
        def to_svg_color(color_in):
            if color_in is None or color_in == "none":
                return "none"
                
            r, g, b, a = parse_color(color_in)
            if a == 0:
                return "none"
                
            if color_mode == Config.EXPORT_OPTIONS['colors'][1]:
                y = int(0.299 * r + 0.587 * g + 0.114 * b)
                r, g, b = y, y, y
            elif color_mode == Config.EXPORT_OPTIONS['colors'][2]:
                y = int(0.299 * r + 0.587 * g + 0.114 * b)
                val = 255 if y >= 127 else 0
                r, g, b = val, val, val
                
            if a == 255:
                return f"rgb({r},{g},{b})"
            else:
                return f"rgba({r},{g},{b},{a/255:.3f})"
            
        # 5. 遍历拦截的绘制命令并转换为 SVG XML 元素
        svg_elements = []
        for cmd in draw_temp.commands:
            t = cmd['type']
            
            if t == 'text':
                cx, cy = cmd['xy']
                tx = (cx - x0) / ssaa_factor + p
                ty = (cy - y0) / ssaa_factor + p
                text_val = cmd['text']
                font = cmd['font']
                fill = to_svg_color(cmd['fill'])
                
                # 获取字体尺寸
                font_sz = getattr(font, 'size', ctx_ssaa['font_size'] * ctx_ssaa['view_scale'])
                font_sz_real = font_sz / ssaa_factor
                
                # 特殊字符转义，保证 XML 合规
                escaped_text = text_val.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                
                svg_elements.append(
                    f'  <text x="{tx:.2f}" y="{ty:.2f}" '
                    f'font-family="Times New Roman, Times, serif" font-size="{font_sz_real:.2f}" '
                    f'fill="{fill}" text-anchor="middle" dominant-baseline="central">{escaped_text}</text>'
                )
                
            elif t == 'line':
                xy = cmd['xy']
                fill = to_svg_color(cmd['fill'])
                width = cmd['width'] / ssaa_factor
                
                # 转换所有坐标点
                pts_transformed = []
                if isinstance(xy, list):
                    if len(xy) > 0:
                        if isinstance(xy[0], tuple):
                            for px, py in xy:
                                pts_transformed.append(((px - x0) / ssaa_factor + p, (py - y0) / ssaa_factor + p))
                        else:
                            for idx in range(0, len(xy), 2):
                                px, py = xy[idx], xy[idx+1]
                                pts_transformed.append(((px - x0) / ssaa_factor + p, (py - y0) / ssaa_factor + p))
                
                if len(pts_transformed) == 2:
                    p1, p2 = pts_transformed
                    svg_elements.append(
                        f'  <line x1="{p1[0]:.2f}" y1="{p1[1]:.2f}" x2="{p2[0]:.2f}" y2="{p2[1]:.2f}" '
                        f'stroke="{fill}" stroke-width="{width:.2f}" stroke-linecap="round" stroke-linejoin="round" />'
                    )
                elif len(pts_transformed) > 2:
                    path_d = "M " + " L ".join(f"{pt[0]:.2f} {pt[1]:.2f}" for pt in pts_transformed)
                    svg_elements.append(
                        f'  <path d="{path_d}" fill="none" stroke="{fill}" stroke-width="{width:.2f}" '
                        f'stroke-linecap="round" stroke-linejoin="round" />'
                    )
                    
            elif t == 'rectangle':
                xy = cmd['xy']
                bx0, by0, bx1, by1 = xy
                nbx0 = (bx0 - x0) / ssaa_factor + p
                nby0 = (by0 - y0) / ssaa_factor + p
                nbx1 = (bx1 - x0) / ssaa_factor + p
                nby1 = (by1 - y0) / ssaa_factor + p
                
                fill = to_svg_color(cmd['fill'])
                outline = to_svg_color(cmd['outline'])
                width = cmd['width'] / ssaa_factor
                
                rect_w = nbx1 - nbx0
                rect_h = nby1 - nby0
                
                svg_elements.append(
                    f'  <rect x="{nbx0:.2f}" y="{nby0:.2f}" width="{rect_w:.2f}" height="{rect_h:.2f}" '
                    f'fill="{fill}" stroke="{outline}" stroke-width="{width:.2f}" />'
                )

        # 6. 处理精美外边框线
        if ctx.get('show_border', True):
            border_w = max(1.0, 2.0 * ctx['view_scale'])
            border_color = to_svg_color("#000000")
            svg_elements.append(
                f'  <rect x="0" y="0" width="{w_sheet}" height="{h_sheet}" '
                f'fill="none" stroke="{border_color}" stroke-width="{border_w:.2f}" />'
            )

        # 7. 组装完整 SVG 内容
        sheet_bg = to_svg_color(ctx['sheet_bg_color'])
        svg_header = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{w_sheet}" height="{h_sheet}" '
            f'viewBox="0 0 {w_sheet} {h_sheet}">\n'
            f'  <rect width="100%" height="100%" fill="{sheet_bg}" />\n'
        )
        svg_footer = "\n</svg>"
        
        return svg_header + "\n".join(svg_elements) + svg_footer
