from view.components.checkerboard import create_checkerboard_image


def test_size_aligned_to_phase_unit():
    img = create_checkerboard_image(1497, 1086)
    w, h = img.size
    assert w % 60 == 0 and h % 60 == 0


def test_corner_colors():
    img = create_checkerboard_image(120, 60)
    assert img.getpixel((0, 0)) == (255, 255, 255, 255)  # light cell
    assert img.getpixel((15, 0)) == (241, 245, 249, 255)  # dark cell


def test_phase_identical_across_sizes():
    offsets = [(0, 0), (14, 0), (7, 23)]
    patterns = []
    for size in [(1500, 1140), (2400, 1740), (5400, 4380)]:
        img = create_checkerboard_image(*size)
        w, h = img.size
        pat = tuple(img.getpixel((w // 2 + dx, h // 2 + dy)) for dx, dy in offsets)
        patterns.append(pat)
    assert patterns[0] == patterns[1] == patterns[2]
