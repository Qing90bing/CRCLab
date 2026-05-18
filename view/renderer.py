from PIL import Image, ImageDraw, ImageFont
from config.constants import Config

class CanvasRenderer:
    """
    图像渲染引擎 - 采用 Pillow 内存绘图技术实现 CRC 运算过程绘制。
    
    在内存中进行画布渲染与元素定位，通过 getbbox() 实现算式图像的边缘裁剪与拼装，
    支持不同缩放倍率下的图像重绘。
    """
    def __init__(self, canvas):
        """
        初始化渲染器。
        :param canvas: tkinter.Canvas 实例（保留作为接口兼容性，内部不再用于直接绘制）。
        """
        self.canvas = canvas

    def _load_font(self, size):
        """
        加载 Times New Roman 矢量字体。
        如果系统不包含该字体，则按顺序尝试加载 fallback_families 列表中的备用字体。
        """
        families = Config.FONTS['fallback_families']
        for family in families:
            try:
                return ImageFont.truetype(family, int(size))
            except IOError:
                continue
        return ImageFont.load_default()

    def _render_raw_formula(self, data, dividend, divisor, q, rows, ctx_ssaa, ssaa_factor):
        """
        在超采样的临时画布上绘制公式并执行 getbbox() 裁剪与缩放。
        
        将超采样绘制与最终的背景填充及边框绘制进行步骤解耦，以实现更好的模块内聚。
        """
        L = self._calculate_layout(ctx_ssaa, dividend, divisor)
        s = L['s']
        
        # 配置临时画布尺寸，以减少内存占用与扫描开销
        w_temp = int(Config.LAYOUT['temp_canvas_base'] * max(1.0, s))
        h_temp = int(Config.LAYOUT['temp_canvas_base'] * max(1.0, s))
        img_temp = Image.new("RGBA", (w_temp, h_temp), (0, 0, 0, 0))
        draw_temp = ImageDraw.Draw(img_temp)
        
        ox = Config.LAYOUT['draw_origin_offset'] * s
        oy = Config.LAYOUT['draw_origin_offset'] * s  # 设置绘图原点偏移，避免内容截断
        
        self._draw_quotient(draw_temp, q, L, ctx_ssaa, ox, oy)
        line_y = self._draw_header_elements(draw_temp, dividend, L, ctx_ssaa, ox, oy)
        self._draw_operands(draw_temp, data, dividend, divisor, line_y, L, ctx_ssaa, ox, oy)
        self._draw_steps(draw_temp, rows, data, line_y, L, ctx_ssaa, ox, oy)
        
        bbox = img_temp.getbbox()
        if not bbox:
            return None
            
        x0, y0, x1, y1 = bbox
        img_formula = img_temp.crop(bbox)
        
        # SSAA 抗锯齿：利用 Lanczos 滤波器对图像进行下采样以平滑边缘
        w_real = int((x1 - x0) / ssaa_factor)
        h_real = int((y1 - y0) / ssaa_factor)
        if w_real > 0 and h_real > 0:
            img_formula = img_formula.resize((w_real, h_real), Image.Resampling.LANCZOS)
            
        return img_formula

    def render(self, data, dividend, divisor, q, rows, ctx):
        """
        渲染入口函数：包含超采样与拼接逻辑。
        
        1. 采用超采样高分辨率绘制所有算式元素；
        2. 裁剪出有效区域并利用 Lanczos 滤波器缩放至物理尺寸以平滑线条；
        3. 拼接到带边距的白色背景纸张中央，并可选择绘制外边框。
        """
        ssaa_factor = Config.LAYOUT['ssaa_factor']
        ctx_ssaa = ctx.copy()
        ctx_ssaa['view_scale'] = ctx['view_scale'] * ssaa_factor
        
        sheet_bg = ctx['sheet_bg_color']
        is_transparent_bg = (sheet_bg in ("transparent", "none"))

        img_formula = self._render_raw_formula(data, dividend, divisor, q, rows, ctx_ssaa, ssaa_factor)
        if not img_formula:
            bg_color = (0, 0, 0, 0) if is_transparent_bg else sheet_bg
            return Image.new("RGBA", (100, 100), bg_color)
            
        # 计算包含 padding 后的纸张最终物理尺寸
        p = int(ctx['padding'] * ctx['view_scale'])
        w_sheet = img_formula.width + 2 * p
        h_sheet = img_formula.height + 2 * p
        
        # 新建 RGBA 纸张并贴入算式
        bg_color = (0, 0, 0, 0) if is_transparent_bg else sheet_bg
        img_sheet = Image.new("RGBA", (w_sheet, h_sheet), bg_color)
            
        img_sheet.paste(img_formula, (p, p), img_formula)
        
        # 绘制纸张外框线
        if ctx.get('show_border', True):
            draw_sheet = ImageDraw.Draw(img_sheet)
            border_w = max(1, int(2 * ctx['view_scale']))
            draw_sheet.rectangle([0, 0, w_sheet - 1, h_sheet - 1], outline="#000000", width=border_w)
        
        return img_sheet

    def _calculate_layout(self, ctx, dividend, divisor):
        """ 集中管理所有几何比例及字体加载 """
        s = ctx['view_scale']
        fs = int(ctx['font_size'] * s)  # 应用缩放后的字体大小
        grid_base = ctx['grid_base'] * s
        
        font = self._load_font(fs)
        
        return {
            's': s,
            'font': font,
            'grid_base': grid_base,
            'cell_w': grid_base * ctx['h_spacing'],             # 单元格宽度（间距调整）
            'cell_h': (grid_base * 1.1) * ctx['v_spacing'],     # 单元格高度（行距调整）
            'line_w': max(1, int(ctx['line_width'] * s)),       # 缩放线宽
            'pad_cells': len(divisor) + 1.0,                    # 为左侧除数留出的空白单元格
            'dividend_len': len(dividend),
            'divisor_len': len(divisor)
        }

    def _draw_quotient(self, draw, q, L, ctx, ox, oy):
        """ 绘制顶部的商 """
        for i, char in enumerate(q):
            cx = ox + (L['pad_cells'] + L['divisor_len'] - 1 + i) * L['cell_w'] + L['cell_w']/2
            cy = oy + L['cell_h'] / 2
            draw.text((cx, cy), text=char, font=L['font'], fill=ctx['digit_color'], anchor="mm")

    def _draw_header_elements(self, draw, dividend, L, ctx, ox, oy):
        """ 绘制主横线与左侧贝塞尔弧线 """
        current_y = L['cell_h']
        line_y = current_y + L['cell_h'] * 0.1
        
        # 计算除数末尾与被除数开头的几何中点，作为弧线交点
        divisor_end_col = L['divisor_len'] - 1
        dividend_start_col = L['pad_cells']
        mid_col = (divisor_end_col + dividend_start_col) / 2
        mid_x = mid_col * L['cell_w'] + L['cell_w']/2
        
        # 微调横线起点
        visual_balance_offset = abs(ctx['curve_span_left'] * L['grid_base']) / 2
        line_left = mid_x + visual_balance_offset + ctx['curve_span_right'] * L['grid_base']
        
        # 计算横线右侧终点
        div_last_x = (L['pad_cells'] + L['dividend_len'] - 1) * L['cell_w'] + L['cell_w']/2
        line_right = div_last_x + L['grid_base'] * 0.6 + ctx['ext_right'] * L['grid_base']
        
        # 绝对定位坐标
        lx0 = ox + line_left
        ly = oy + line_y
        lx1 = ox + line_right
        
        # 1. 绘制主横线
        draw.line([(lx0, ly), (lx1, ly)], fill=ctx['line_color'], width=L['line_w'])
        
        # 2. 绘制左侧贝塞尔弧线
        self._draw_bezier_curve(draw, lx0, ly, L, ctx)
        return line_y

    def _draw_bezier_curve(self, draw, lx0, ly, L, ctx):
        """ 绘制平滑除法贝塞尔曲线 """
        p3x, p3y = lx0, ly
        p0x = lx0 + L['grid_base'] * ctx['curve_span_left']
        p0y = (ly + L['cell_h'] * 0.1) + L['cell_h'] * 0.8
        p1x, p1y = lx0 - L['grid_base'] * 0.2, p0y - L['cell_h'] * 0.2
        p2x, p2y = lx0 + L['grid_base'] * 0.1, ly + L['cell_h'] * 0.3
        
        pts = []
        segments = Config.LAYOUT['curve_segments']
        for i in range(segments + 1):
            t = i / float(segments)
            x = (1-t)**3 * p0x + 3*((1-t)**2)*t * p1x + 3*(1-t)*(t**2) * p2x + (t**3) * p3x
            y = (1-t)**3 * p0y + 3*((1-t)**2)*t * p1y + 3*(1-t)*(t**2) * p2y + (t**3) * p3y
            pts.append((x, y))
            
        draw.line(pts, fill=ctx['line_color'], width=L['line_w'], joint="round")

    def _draw_operands(self, draw, data, dividend, divisor, line_y, L, ctx, ox, oy):
        """ 绘制除数、被除数及灰色补零标记背景块 """
        text_y = line_y + L['cell_h'] * 0.1
        cy = text_y + L['cell_h']/2
        
        # 1. 优先绘制补零标记背景块（RGBA 柔和半透明，若为透明则跳过绘制）
        pad_idx = len(data)
        if pad_idx < len(dividend) and ctx['bg_block_color'] not in ("transparent", "none"):
            bx0 = ox + (L['pad_cells'] + pad_idx) * L['cell_w'] + L['grid_base'] * 0.15
            bx1 = ox + (L['pad_cells'] + len(dividend)) * L['cell_w'] - L['grid_base'] * 0.15
            by0 = oy + text_y + L['cell_h']*0.05
            by1 = oy + text_y + L['cell_h']*0.95
            draw.rectangle([bx0, by0, bx1, by1], fill=ctx['bg_block_color'], outline=None)

        # 2. 绘制左侧除数
        for i, char in enumerate(divisor):
            cx = ox + i * L['cell_w'] + L['cell_w']/2
            draw.text((cx, oy + cy), text=char, font=L['font'], fill=ctx['digit_color'], anchor="mm")

        # 3. 绘制右侧被除数
        for i, char in enumerate(dividend):
            cx = ox + (L['pad_cells'] + i) * L['cell_w'] + L['cell_w']/2
            color = ctx['bg_digit_color'] if i >= pad_idx else ctx['digit_color']
            draw.text((cx, oy + cy), text=char, font=L['font'], fill=color, anchor="mm")

    def _draw_steps(self, draw, rows, data, line_y, L, ctx, ox, oy):
        """ 顺序绘制 CRC 异或计算中间行与横线 """
        curr_y = line_y + L['cell_h'] * 1.1
        
        for row in rows:
            if row['type'] == 'line':
                # 绘制中间的减法（异或）横线
                curr_y += L['cell_h'] * 0.1
                lx0 = ox + (L['pad_cells'] + row['offset']) * L['cell_w'] + L['grid_base'] * 0.15 + ctx['ext_left'] * L['grid_base']
                lx1 = ox + (L['pad_cells'] + row['offset'] + row['len']) * L['cell_w'] - L['grid_base'] * 0.15 + ctx['ext_right'] * L['grid_base']
                ly = oy + curr_y
                draw.line([(lx0, ly), (lx1, ly)], fill=ctx['line_color'], width=L['line_w'])
                curr_y += L['cell_h'] * 0.1
            else:
                # 绘制数据行或余数行
                self._draw_single_step_row(draw, row, data, curr_y, L, ctx, ox, oy)
                curr_y += L['cell_h']

    def _draw_single_step_row(self, draw, row, data, cy_base, L, ctx, ox, oy):
        """ 绘制单个异或数值行 """
        cy = cy_base + L['cell_h']/2
        
        # 1. 绘制余数行的补零灰色标记块（若为透明则跳过绘制）
        if row['type'] == 'remainder' and ctx['bg_block_color'] not in ("transparent", "none"):
            pad_s = len(data) - row['offset']
            if 0 <= pad_s < len(row['val']):
                bx0 = ox + (L['pad_cells'] + row['offset'] + pad_s) * L['cell_w'] + L['grid_base'] * 0.15
                bx1 = ox + (L['pad_cells'] + row['offset'] + len(row['val'])) * L['cell_w'] - L['grid_base'] * 0.15
                by0 = oy + cy_base + L['cell_h']*0.05
                by1 = oy + cy_base + L['cell_h']*0.95
                draw.rectangle([bx0, by0, bx1, by1], fill=ctx['bg_block_color'], outline=None)

        # 2. 绘制该行中的二进制数字
        for i, char in enumerate(row['val']):
            cx = ox + (L['pad_cells'] + row['offset'] + i) * L['cell_w'] + L['cell_w']/2
            color = ctx['digit_color']
            # 被拉下来的补零数字显示特殊颜色
            if row['type'] == 'remainder' and i >= (len(data) - row['offset']):
                color = ctx['bg_digit_color']
            draw.text((cx, oy + cy), text=char, font=L['font'], fill=color, anchor="mm")

    def _fill_checkerboard(self, img, size=10):
        """ 在图像底板上用柔和灰白棋盘格填充，指示预览状态下的透明背景 """
        draw = ImageDraw.Draw(img)
        w, h = img.size
        for x in range(0, w, size):
            for y in range(0, h, size):
                if ((x // size) + (y // size)) % 2 == 1:
                    # 使用非常雅致微弱的浅灰色
                    draw.rectangle([x, y, x + size - 1, y + size - 1], fill="#f1f5f9", outline=None)
                else:
                    draw.rectangle([x, y, x + size - 1, y + size - 1], fill="#ffffff", outline=None)
