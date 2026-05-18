from PIL import Image, ImageDraw
from config.constants import Config

class SVGInterceptDraw:
    """
    绘图指令拦截器代理类。
    用于在内存中绘制 Pillow 图像的同时拦截记录 text、line 和 rectangle 命令。
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
    SVG 渲染转换器。
    
    使用 CanvasRenderer 进行排版，
    将拦截到的绘图指令转换为 SVG 1.1 格式的 XML 文本。
    """
    @staticmethod
    def render_to_svg(renderer, data, dividend, divisor, q, rows, ctx):
        """
        渲染 CRC 长除法步骤并生成 SVG 格式的字符串。
        复用 CanvasRenderer 实例的绘制逻辑，以保持与预览界面一致。
        """
        ssaa_factor = Config.LAYOUT['ssaa_factor']
        ctx_ssaa = ctx.copy()
        ctx_ssaa['view_scale'] = ctx['view_scale'] * ssaa_factor

        # 1. 临时画布与拦截器初始化
        L = renderer._calculate_layout(ctx_ssaa, dividend, divisor)
        s = L['s']
        
        w_temp = int(Config.LAYOUT['temp_canvas_base'] * max(1.0, s))
        h_temp = int(Config.LAYOUT['temp_canvas_base'] * max(1.0, s))
        img_temp = Image.new("RGBA", (w_temp, h_temp), (0, 0, 0, 0))
        draw_real = ImageDraw.Draw(img_temp)
        draw_temp = SVGInterceptDraw(draw_real)
        
        ox = Config.LAYOUT['draw_origin_offset'] * s
        oy = Config.LAYOUT['draw_origin_offset'] * s
        
        # 2. 执行几何绘制指令
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

        # Helper: 转换并应用灰度/黑白滤镜，输出兼容的 (hex_color, opacity_val)
        color_mode = ctx.get('color_mode', Config.EXPORT_OPTIONS['colors'][0])
        
        def to_svg_color_and_opacity(color_in):
            """
            解析并应用色彩滤镜，将颜色统一解耦输出为 (hex_color, opacity_val) 元组。
            这有助于在不支持 rgba() 解析的环境中正确渲染，避免纯黑块的渲染。
            """
            if color_in is None or color_in == "none":
                return "none", 1.0
                
            r, g, b, a = parse_color(color_in)
            if a == 0:
                return "none", 0.0
                
            if color_mode == Config.EXPORT_OPTIONS['colors'][1]:
                y = int(0.299 * r + 0.587 * g + 0.114 * b)
                r, g, b = y, y, y
            elif color_mode == Config.EXPORT_OPTIONS['colors'][2]:
                y = int(0.299 * r + 0.587 * g + 0.114 * b)
                val = 255 if y >= 127 else 0
                r, g, b = val, val, val
                
            hex_color = f"#{r:02x}{g:02x}{b:02x}"
            opacity = a / 255.0
            return hex_color, opacity
            
        # 5. 遍历拦截的绘制命令并转换为 SVG XML 元素
        svg_elements = []
        for cmd in draw_temp.commands:
            t = cmd['type']
            
            if t == 'text':
                cx, cy = cmd['xy']
                tx = (cx - x0) / ssaa_factor + p
                
                text_val = cmd['text']
                font = cmd['font']
                fill_color, fill_op = to_svg_color_and_opacity(cmd['fill'])
                
                # 获取字体尺寸并微调真实坐标
                font_sz = getattr(font, 'size', ctx_ssaa['font_size'] * ctx_ssaa['view_scale'])
                font_sz_real = font_sz / ssaa_factor
                
                # 基线偏移补偿：通过 y' = y + 0.33 * FontSize 调整垂直居中对齐
                ty = (cy - y0) / ssaa_factor + p + 0.33 * font_sz_real
                
                # 特殊字符转义，保证 XML 合规
                escaped_text = text_val.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                
                fill_attrs = f'fill="{fill_color}"'
                if fill_op < 1.0 and fill_color != "none":
                    fill_attrs += f' fill-opacity="{fill_op:.3f}"'
                
                svg_elements.append(
                    f'  <text x="{tx:.2f}" y="{ty:.2f}" '
                    f'font-family="Times New Roman, Times, serif" font-size="{font_sz_real:.2f}" '
                    f'{fill_attrs} text-anchor="middle">{escaped_text}</text>'
                )
                
            elif t == 'line':
                xy = cmd['xy']
                stroke_color, stroke_op = to_svg_color_and_opacity(cmd['fill'])
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
                
                stroke_attrs = f'stroke="{stroke_color}"'
                if stroke_op < 1.0 and stroke_color != "none":
                    stroke_attrs += f' stroke-opacity="{stroke_op:.3f}"'
                
                if len(pts_transformed) == 2:
                    p1, p2 = pts_transformed
                    svg_elements.append(
                        f'  <line x1="{p1[0]:.2f}" y1="{p1[1]:.2f}" x2="{p2[0]:.2f}" y2="{p2[1]:.2f}" '
                        f'{stroke_attrs} stroke-width="{width:.2f}" stroke-linecap="round" stroke-linejoin="round" />'
                    )
                elif len(pts_transformed) > 2:
                    path_d = "M " + " L ".join(f"{pt[0]:.2f} {pt[1]:.2f}" for pt in pts_transformed)
                    svg_elements.append(
                        f'  <path d="{path_d}" fill="none" {stroke_attrs} stroke-width="{width:.2f}" '
                        f'stroke-linecap="round" stroke-linejoin="round" />'
                    )
                    
            elif t == 'rectangle':
                xy = cmd['xy']
                bx0, by0, bx1, by1 = xy
                nbx0 = (bx0 - x0) / ssaa_factor + p
                nby0 = (by0 - y0) / ssaa_factor + p
                nbx1 = (bx1 - x0) / ssaa_factor + p
                nby1 = (by1 - y0) / ssaa_factor + p
                
                fill_color, fill_op = to_svg_color_and_opacity(cmd['fill'])
                outline_color, stroke_op = to_svg_color_and_opacity(cmd['outline'])
                width = cmd['width'] / ssaa_factor
                
                rect_w = nbx1 - nbx0
                rect_h = nby1 - nby0
                
                fill_attrs = f'fill="{fill_color}"'
                if fill_op < 1.0 and fill_color != "none":
                    fill_attrs += f' fill-opacity="{fill_op:.3f}"'
                
                stroke_attrs = f'stroke="{outline_color}"'
                if stroke_op < 1.0 and outline_color != "none":
                    stroke_attrs += f' stroke-opacity="{stroke_op:.3f}"'
                
                svg_elements.append(
                    f'  <rect x="{nbx0:.2f}" y="{nby0:.2f}" width="{rect_w:.2f}" height="{rect_h:.2f}" '
                    f'{fill_attrs} {stroke_attrs} stroke-width="{width:.2f}" />'
                )

        # 6. 绘制外边框线
        if ctx.get('show_border', True):
            border_w = max(1.0, 2.0 * ctx['view_scale'])
            border_color, border_op = to_svg_color_and_opacity("#000000")
            border_attrs = f'stroke="{border_color}"'
            if border_op < 1.0 and border_color != "none":
                border_attrs += f' stroke-opacity="{border_op:.3f}"'
            svg_elements.append(
                f'  <rect x="0" y="0" width="{w_sheet}" height="{h_sheet}" '
                f'fill="none" {border_attrs} stroke-width="{border_w:.2f}" />'
            )

        # 7. 组装完整 SVG 内容
        sheet_bg_color, sheet_bg_op = to_svg_color_and_opacity(ctx['sheet_bg_color'])
        sheet_bg_attrs = f'fill="{sheet_bg_color}"'
        if sheet_bg_op < 1.0 and sheet_bg_color != "none":
            sheet_bg_attrs += f' fill-opacity="{sheet_bg_op:.3f}"'
            
        svg_header = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{w_sheet}" height="{h_sheet}" '
            f'viewBox="0 0 {w_sheet} {h_sheet}">\n'
            f'  <rect width="100%" height="100%" {sheet_bg_attrs} />\n'
        )
        svg_footer = "\n</svg>"
        
        return svg_header + "\n".join(svg_elements) + svg_footer
