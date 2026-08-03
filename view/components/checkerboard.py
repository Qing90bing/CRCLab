from PIL import Image, ImageDraw
from config.constants import Config


def create_checkerboard_image(width, height):
    """
    按指定物理尺寸生成灰白棋盘格背景图（RGBA）。
    颜色与格子尺寸均读取自 Config.CHECKERBOARD，避免硬编码散落各处。
    浅色格子作为底图基色，仅在奇数格子绘制深色矩形。
    尺寸会向上取整到 4 倍格子大小的倍数，保证任意尺寸重建时棋盘格相对屏幕的相位不变。
    """
    cfg = Config.CHECKERBOARD
    size = cfg['cell']
    light = cfg['color_light']
    dark = cfg['color_dark']
    # 相位对齐：尺寸取整到 4 倍格子大小的倍数，任意重建时图案相位不变
    align = 4 * size  # 相位对齐单位：两对格子的周期，确保重建时图案相位不变
    w = max(align, ((int(width) + align - 1) // align) * align)
    h = max(align, ((int(height) + align - 1) // align) * align)

    img = Image.new("RGBA", (w, h), light)
    draw = ImageDraw.Draw(img)
    for x in range(0, w, size):
        for y in range(0, h, size):
            if ((x // size) + (y // size)) % 2 == 1:
                draw.rectangle([x, y, x + size - 1, y + size - 1], fill=dark, outline=None)
    return img
