"""
日签海报图生成（Pillow）
"""
import os

from PIL import Image, ImageDraw, ImageFont

BG = '#F7F7F5'
TEXT = '#111111'
SUB = '#707070'
LINE = '#D9D9D5'
PRIMARY_DARK = '#5F93AB'

FONT_CANDIDATES = [
    'shijing_things/static/fonts/NotoSerifCJKsc-Regular.otf',
    '/System/Library/Fonts/Supplemental/Songti.ttc',
    '/System/Library/Fonts/PingFang.ttc',
]

_font_cache = {}


def _font(size: int) -> ImageFont.FreeTypeFont:
    if size in _font_cache:
        return _font_cache[size]
    font = None
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            try:
                font = ImageFont.truetype(path, size)
                break
            except Exception:
                continue
    if font is None:
        font = ImageFont.load_default()
    _font_cache[size] = font
    return font


def _text_w(draw, text, font):
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0]


def _center(draw, cx, y, text, font, fill):
    draw.text((cx - _text_w(draw, text, font) / 2, y), text, font=font, fill=fill)


def make_daily_poster(item_name: str, category: str, quote: str,
                      section: str, title: str, image_path: str,
                      date_str: str) -> bytes:
    """生成日签 PNG，返回字节"""
    import io

    W, H = 900, 1280
    canvas = Image.new('RGB', (W, H), BG)
    draw = ImageDraw.Draw(canvas)

    # 顶部：栏目 + 日期
    f_small = _font(22)
    draw.text((60, 52), '每日名物', font=f_small, fill=SUB)
    draw.text((W - 60 - _text_w(draw, date_str, f_small), 52), date_str,
              font=f_small, fill=SUB)
    draw.line((60, 96, W - 60, 96), fill=LINE, width=1)

    # 古画（等比缩放放入 780x640 画框，带发丝边框）
    frame_x, frame_y, frame_w, frame_h = 60, 130, W - 120, 640
    art = Image.open(image_path).convert('RGB')
    scale = min(frame_w / art.width, frame_h / art.height)
    art = art.resize((int(art.width * scale), int(art.height * scale)),
                     Image.LANCZOS)
    ax = frame_x + (frame_w - art.width) // 2
    ay = frame_y + (frame_h - art.height) // 2
    canvas.paste(art, (ax, ay))
    draw.rectangle((ax - 1, ay - 1, ax + art.width, ay + art.height),
                   outline=LINE, width=1)

    # 名物名 + 类目
    y = frame_y + frame_h + 42
    _center(draw, W / 2, y, item_name, _font(64), TEXT)
    y += 96
    _center(draw, W / 2, y, f'{category}类', _font(24), SUB)

    # 引文 + 出处
    y += 66
    _center(draw, W / 2, y, f'「{quote}」', _font(32), PRIMARY_DARK)
    y += 62
    _center(draw, W / 2, y, f'——《{section}·{title}》', _font(24), SUB)

    # 底部
    draw.line((60, H - 96, W - 60, H - 96), fill=LINE, width=1)
    _center(draw, W / 2, H - 72, '诗经物什 · 多识于鸟兽草木之名', _font(22), SUB)

    buf = io.BytesIO()
    canvas.save(buf, format='PNG')
    return buf.getvalue()
