import tkinter as tk
from tkinter import font as tkfont

class CanvasRenderer:
    """
    视觉渲染引擎 - 负责 CRC 运算过程在 Canvas 上的几何绘制。
    
    遵循职责单一原则，本引擎不维护任何状态，仅根据传入的渲染上下文 (ctx) 
    和运算数据 (rows) 进行线性绘制。支持实时缩放、平移和样式动态调整。
    """
    def __init__(self, canvas):
        """
        初始化渲染器。
        :param canvas: tkinter.Canvas 实例，用于绘图。
        """
        self.canvas = canvas

    def render(self, data, dividend, divisor, q, rows, ctx):
        """
        主渲染入口：采用流水线模式组织绘制流程。
        
        绘制顺序（层级从底向上）：
        1. 清除画布与同步背景色。
        2. 预计算布局参数 (L)。
        3. 绘制顶部商 (q)。
        4. 绘制标题元素（主横线、贝塞尔弧线）。
        5. 绘制除数与被除数（含补零标记块）。
        6. 遍历运算步骤绘制中间过程与余数。
        7. 最终背景修饰与滚动域同步。
        """
        self.canvas.delete("all")
        self.canvas.config(bg=ctx['canvas_bg_color'])
        
        # 1. 预计算布局参数：将缩放因子应用到所有几何属性上
        L = self._calculate_layout(ctx, dividend, divisor)
        
        # 2. 依次绘制各组件
        self._draw_quotient(q, L, ctx)
        line_y = self._draw_header_elements(dividend, L, ctx)
        self._draw_operands(data, dividend, divisor, line_y, L, ctx)
        self._draw_steps(rows, data, line_y, L, ctx)
        
        # 3. 最终背景修饰：在所有元素下方绘制一个白色“纸张”矩形
        self._finalize_canvas(ctx)

    def _calculate_layout(self, ctx, dividend, divisor):
        """
        集中管理所有几何比例计算。
        
        缩放逻辑：所有长度单位（grid_base, cell_w, cell_h）都会乘以 ctx['view_scale']。
        """
        s = ctx['view_scale']
        fs = int(ctx['font_size'] * s)  # 缩放后的字体大小
        grid_base = ctx['grid_base'] * s
        return {
            's': s,
            'font': tkfont.Font(family="Times New Roman", size=fs),
            'grid_base': grid_base,
            'cell_w': grid_base * ctx['h_spacing'],  # 单元格宽度（考虑字符间距）
            'cell_h': (grid_base * 1.1) * ctx['v_spacing'],  # 单元格高度（考虑行间距）
            'line_w': max(1, int(ctx['line_width'] * s)), # 缩放后的线宽
            'pad_cells': len(divisor) + 1.0,  # 为左侧除数留出的空白单元格数量
            'dividend_len': len(dividend),
            'divisor_len': len(divisor)
        }

    def _draw_quotient(self, q, L, ctx):
        """ 绘制顶部的商 """
        for i, char in enumerate(q):
            # 商的 X 坐标需与被除数起始位置对齐，但需考虑计算偏移
            cx = (L['pad_cells'] + L['divisor_len'] - 1 + i) * L['cell_w'] + L['cell_w']/2
            cy = L['cell_h'] / 2
            self.canvas.create_text(cx, cy, text=char, font=L['font'], fill=ctx['digit_color'])

    def _draw_header_elements(self, dividend, L, ctx):
        """ 绘制主横线与左侧弧线 - 实现基于几何的中点对齐 """
        current_y = L['cell_h']
        line_y = current_y + L['cell_h'] * 0.1
        
        # 智能居中算法：计算除数末尾与被除数开头的几何中点，作为弧线的交点
        divisor_end_col = L['divisor_len'] - 1
        dividend_start_col = L['pad_cells']
        mid_col = (divisor_end_col + dividend_start_col) / 2
        mid_x = mid_col * L['cell_w'] + L['cell_w']/2
        
        # 视觉平衡修正：根据用户设置的跨度参数微调横线起点
        visual_balance_offset = abs(ctx['curve_span_left'] * L['grid_base']) / 2
        line_left = mid_x + visual_balance_offset + ctx['curve_span_right'] * L['grid_base']
        
        # 计算横线终点
        div_last_x = (L['pad_cells'] + L['dividend_len'] - 1) * L['cell_w'] + L['cell_w']/2
        line_right = div_last_x + L['grid_base'] * 0.6 + ctx['ext_right'] * L['grid_base']
        
        # 绘制主横线
        self.canvas.create_line(line_left, line_y, line_right, line_y, 
                               width=L['line_w'], capstyle=tk.ROUND, fill=ctx['line_color'])
        
        # 绘制贝塞尔弧线
        self._draw_bezier_curve(line_left, line_y, L, ctx)
        return line_y

    def _draw_bezier_curve(self, line_left, line_y, L, ctx):
        """ 
        绘制贝塞尔弧线。
        
        使用三阶贝塞尔曲线模拟手绘除法符号的弧度感。
        p0: 起点 (下方), p1/p2: 控制点, p3: 终点 (横线左端)
        """
        p3x, p3y = line_left, line_y
        p0x = line_left + L['grid_base'] * ctx['curve_span_left']
        p0y = (line_y + L['cell_h'] * 0.1) + L['cell_h'] * 0.8
        p1x, p1y = line_left - L['grid_base'] * 0.2, p0y - L['cell_h'] * 0.2
        p2x, p2y = line_left + L['grid_base'] * 0.1, line_y + L['cell_h'] * 0.3
        
        pts = []
        for i in range(41):
            t = i / 40.0
            # 三阶贝塞尔曲线公式
            x = (1-t)**3 * p0x + 3*((1-t)**2)*t * p1x + 3*(1-t)*(t**2) * p2x + (t**3) * p3x
            y = (1-t)**3 * p0y + 3*((1-t)**2)*t * p1y + 3*(1-t)*(t**2) * p2y + (t**3) * p3y
            pts.extend([x, y])
        self.canvas.create_line(pts, smooth=True, width=L['line_w'], capstyle=tk.ROUND, fill=ctx['line_color'])

    def _draw_operands(self, data, dividend, divisor, line_y, L, ctx):
        """ 绘制除数、被除数及灰色标记块 """
        text_y = line_y + L['cell_h'] * 0.1
        cy = text_y + L['cell_h']/2
        
        # 1. 绘制除数
        for i, char in enumerate(divisor):
            cx = i * L['cell_w'] + L['cell_w']/2
            self.canvas.create_text(cx, cy, text=char, font=L['font'], fill=ctx['digit_color'])

        # 2. 补零标记背景块（若开启）
        pad_idx = len(data)
        if ctx['show_gray'] and pad_idx < len(dividend):
            bx0 = (L['pad_cells'] + pad_idx) * L['cell_w'] + L['grid_base'] * 0.15
            bx1 = (L['pad_cells'] + len(dividend)) * L['cell_w'] - L['grid_base'] * 0.15
            self.canvas.create_rectangle(bx0, text_y + L['cell_h']*0.05, bx1, text_y + L['cell_h']*0.95, 
                                        fill=ctx['bg_block_color'], outline="")

        # 3. 绘制被除数
        for i, char in enumerate(dividend):
            cx = (L['pad_cells'] + i) * L['cell_w'] + L['cell_w']/2
            # 补零部分的数字使用特殊颜色
            color = ctx['bg_digit_color'] if (ctx['show_gray'] and i >= pad_idx) else ctx['digit_color']
            self.canvas.create_text(cx, cy, text=char, font=L['font'], fill=color)

    def _draw_steps(self, rows, data, line_y, L, ctx):
        """ 绘制所有的运算步骤行 """
        curr_y = line_y + L['cell_h'] * 1.1
        
        for row in rows:
            if row['type'] == 'line':
                # 绘制中间的异或横线
                curr_y += L['cell_h'] * 0.1
                lx0 = (L['pad_cells'] + row['offset']) * L['cell_w'] + L['grid_base'] * 0.15 + ctx['ext_left'] * L['grid_base']
                lx1 = (L['pad_cells'] + row['offset'] + row['len']) * L['cell_w'] - L['grid_base'] * 0.15 + ctx['ext_right'] * L['grid_base']
                self.canvas.create_line(lx0, curr_y, lx1, curr_y, width=L['line_w'], capstyle=tk.ROUND, fill=ctx['line_color'])
                curr_y += L['cell_h'] * 0.1
            else:
                # 绘制普通数据行或余数行
                self._draw_single_step_row(row, data, curr_y, L, ctx)
                curr_y += L['cell_h']

    def _draw_single_step_row(self, row, data, cy_base, L, ctx):
        """ 绘制单个数据行（包含余数背景块处理） """
        cy = cy_base + L['cell_h']/2
        
        # 针对余数行，也需要绘制补零背景块
        if row['type'] == 'remainder' and ctx['show_gray']:
            pad_s = len(data) - row['offset']
            if 0 <= pad_s < len(row['val']):
                bx0 = (L['pad_cells'] + row['offset'] + pad_s) * L['cell_w'] + L['grid_base'] * 0.15
                bx1 = (L['pad_cells'] + row['offset'] + len(row['val'])) * L['cell_w'] - L['grid_base'] * 0.15
                self.canvas.create_rectangle(bx0, cy_base+L['cell_h']*0.05, bx1, cy_base+L['cell_h']*0.95, fill=ctx['bg_block_color'], outline="")

        # 逐个绘制字符
        for i, char in enumerate(row['val']):
            cx = (L['pad_cells'] + row['offset'] + i) * L['cell_w'] + L['cell_w']/2
            color = ctx['digit_color']
            # 余数行中属于补零部分的位，使用特殊颜色
            if row['type'] == 'remainder' and ctx['show_gray'] and i >= (len(data) - row['offset']):
                color = ctx['bg_digit_color']
            self.canvas.create_text(cx, cy, text=char, font=L['font'], fill=color)

    def _finalize_canvas(self, ctx):
        """ 
        纸张背景修饰与滚动域同步。
        
        该方法计算所有已绘制元素的边界，并在其下方绘制一个带边框的白色矩形，
        模拟出纸张打印的效果，并同步 Canvas 的可滚动区域。
        """
        bbox = self.canvas.bbox("all")
        if bbox:
            p = ctx['padding'] * ctx['view_scale']
            # 创建模拟纸张的背景
            sid = self.canvas.create_rectangle(bbox[0]-p, bbox[1]-p, bbox[2]+p, bbox[3]+p, 
                                              fill=ctx['sheet_bg_color'], outline="#1e293b", 
                                              width=max(1, int(2*ctx['view_scale'])))
            self.canvas.tag_lower(sid) # 确保矩形在最底层
        
        # 设置一个巨大的滚动范围，配合 view_moveto 实现画布自由拖拽
        self.canvas.config(scrollregion=(-3000, -3000, 3000, 3000))
