"""실시간 가격 결과를 공유용 4:5 PNG 단가표로 생성한다."""

from datetime import datetime
from io import BytesIO
from pathlib import Path
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw, ImageFont


WIDTH = 1080
HEIGHT = 1350


def _first_available_font(*candidates):
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return path
    raise RuntimeError("PNG 생성에 사용할 한글 글꼴을 찾을 수 없습니다.")


FONT_REGULAR = _first_available_font(
    r"C:\Windows\Fonts\malgun.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJKkr-Regular.otf",
    "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
)
FONT_BOLD = _first_available_font(
    r"C:\Windows\Fonts\malgunbd.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJKkr-Bold.otf",
    "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
)


def _font(size, bold=False):
    path = FONT_BOLD if bold else FONT_REGULAR
    return ImageFont.truetype(str(path), size=size)


def _fit_text(draw, text, max_width, start_size=34, min_size=22, bold=False):
    for size in range(start_size, min_size - 1, -1):
        font = _font(size, bold=bold)
        if draw.textbbox((0, 0), text, font=font)[2] <= max_width:
            return font
    return _font(min_size, bold=bold)


def _fit_or_wrap_text(draw, text, max_width):
    """상품명을 우선 한 줄로 맞추고, 불가능하면 최대 두 줄로 나눈다."""
    one_line_font = _fit_text(draw, text, max_width, start_size=31, min_size=24, bold=True)
    if draw.textbbox((0, 0), text, font=one_line_font)[2] <= max_width:
        return [text], one_line_font

    best_lines = None
    best_score = None
    for split_at in range(1, len(text)):
        first = text[:split_at].rstrip()
        second = text[split_at:].lstrip()
        if not first or not second:
            continue
        score = abs(len(first) - len(second))
        if text[split_at - 1].isspace() or text[split_at].isspace():
            score -= 8
        if best_score is None or score < best_score:
            best_lines = [first, second]
            best_score = score

    for size in range(24, 19, -1):
        font = _font(size, bold=True)
        if all(draw.textbbox((0, 0), line, font=font)[2] <= max_width for line in best_lines):
            return best_lines, font
    return best_lines, _font(20, bold=True)


def _draw_paper_texture(draw):
    """가독성을 해치지 않는 미세한 한지 결을 직접 그린다."""
    for y in range(18, HEIGHT, 31):
        offset = (y * 7) % 29
        for x in range(offset, WIDTH, 47):
            draw.line((x, y, x + 16, y + 1), fill="#ebe5d8", width=1)


def _draw_livestock_motif(draw):
    """외부 이미지 없이 원육 단면과 소 라인 실루엣을 구성한다."""
    # 옅은 원육 단면과 마블링
    draw.ellipse((784, 44, 1038, 276), fill="#eadbd2", outline="#d8bdad", width=2)
    draw.ellipse((820, 76, 1008, 245), fill="#f3e8df")
    draw.arc((832, 91, 1001, 222), 205, 344, fill="#cda99a", width=4)
    draw.arc((805, 69, 977, 248), 28, 155, fill="#dbc2b5", width=3)
    draw.line((872, 100, 931, 224), fill="#d8bdad", width=3)
    draw.line((829, 168, 984, 132), fill="#d8bdad", width=3)

    # 소의 윤곽을 기하학적 라인으로 절제해 표현
    cow = [(803, 178), (838, 151), (892, 143), (936, 157), (975, 150), (1005, 169)]
    draw.line(cow, fill="#b18b49", width=3, joint="curve")
    draw.line((832, 178, 839, 204, 849, 204), fill="#b18b49", width=3)
    draw.line((947, 174, 955, 203, 965, 203), fill="#b18b49", width=3)
    draw.line((1003, 168, 1017, 159, 1025, 166), fill="#b18b49", width=3)


def _draw_price_row(draw, rank, product, top, row_height, colors):
    dark_green, gold, ink, muted, white = colors
    bottom = top + row_height
    first = rank == 1
    draw.rounded_rectangle(
        (72, top, 1008, bottom),
        radius=18,
        fill="#fbf5e8" if first else white,
        outline="#c9a55d" if first else "#ded9cc",
        width=3 if first else 1,
    )
    if first:
        draw.rounded_rectangle((72, top, 81, bottom), radius=5, fill=gold)

    badge_left = 96
    badge_top = top + (row_height - 54) / 2
    draw.ellipse(
        (badge_left, badge_top, badge_left + 54, badge_top + 54),
        fill=dark_green if first else "#eee9dc",
    )
    rank_font = _font(23, bold=True)
    draw.text(
        (badge_left + 27, badge_top + 27),
        str(rank),
        font=rank_font,
        fill="#fffaf0" if first else gold,
        anchor="mm",
    )

    label = str(product["label"])
    label_lines, label_font = _fit_or_wrap_text(draw, label, 500)
    if len(label_lines) == 1:
        draw.text(
            (174, top + row_height / 2), label_lines[0],
            font=label_font, fill=ink, anchor="lm",
        )
    else:
        line_height = label_font.size + 4
        first_y = top + row_height / 2 - line_height / 2
        for index, line in enumerate(label_lines):
            draw.text(
                (174, first_y + index * line_height), line,
                font=label_font, fill=ink, anchor="lm",
            )

    price_text = f"{product['kg_price']:,.0f}원/kg"
    price_font = _font(43 if first else 40, bold=True)
    draw.text(
        (980, top + row_height / 2),
        price_text,
        font=price_font,
        fill=gold if first else dark_green,
        anchor="rm",
    )


def create_price_card_png(menu_name, products, queried_at=None):
    """현재 정렬된 실시간 가격을 1080×1350 PNG 바이트로 반환한다."""
    queried_at = queried_at or datetime.now(ZoneInfo("Asia/Seoul"))
    canvas = Image.new("RGB", (WIDTH, HEIGHT), "#f7f3e9")
    draw = ImageDraw.Draw(canvas)

    dark_green = "#123c2e"
    gold = "#a57a2c"
    ink = "#17231d"
    muted = "#68716b"
    white = "#fffdf8"
    colors = (dark_green, gold, ink, muted, white)

    _draw_paper_texture(draw)
    draw.rectangle((0, 0, 18, HEIGHT), fill=dark_green)
    draw.rectangle((18, 0, 23, HEIGHT), fill=gold)
    _draw_livestock_motif(draw)

    draw.text((72, 58), "도토리다판다", font=_font(25, bold=True), fill=gold)
    draw.text((72, 112), f"{menu_name} 실시간 단가표", font=_font(57, bold=True), fill=dark_green)
    draw.text(
        (72, 190),
        "메뉴에 맞는 원육과 실시간 시세를 한눈에",
        font=_font(25),
        fill=ink,
    )
    timestamp = queried_at.strftime("%Y.%m.%d %H:%M 기준")
    draw.text((72, 238), timestamp, font=_font(23), fill=muted)
    draw.line((72, 294, 1008, 294), fill="#d8cfbc", width=2)

    draw.text((72, 350), "kg당 가격 낮은 순", font=_font(25, bold=True), fill=ink)

    visible_products = products[:5]
    list_top = 395
    list_height = 565
    row_gap = 11
    product_count = max(len(visible_products), 1)
    row_height = min(105, (list_height - row_gap * (product_count - 1)) / product_count)
    rows_height = row_height * product_count + row_gap * (product_count - 1)
    row_top = list_top + (list_height - rows_height) / 2
    for rank, product in enumerate(visible_products, start=1):
        top = row_top + (rank - 1) * (row_height + row_gap)
        _draw_price_row(draw, rank, product, top, row_height, colors)

    # 조회 근거와 변동 안내
    info_top = 982
    draw.line((72, info_top, 1008, info_top), fill="#d8cfbc", width=2)
    draw.text((72, info_top + 24), "금천미트 실시간 조회", font=_font(22, bold=True), fill=dark_green)
    draw.text(
        (72, info_top + 61),
        "가격과 재고는 실시간으로 변동될 수 있으며, 표시 가격은 조회 시점 기준입니다.",
        font=_font(21),
        fill=muted,
    )

    # 정보 중심의 절제된 가입 안내 박스
    hook_top = 1090
    draw.rounded_rectangle(
        (72, hook_top, 1008, 1268),
        radius=20,
        fill="#edf0e9",
        outline="#c8d0c7",
        width=2,
    )
    draw.rectangle((72, hook_top + 24, 78, hook_top + 154), fill=gold)
    draw.text((102, hook_top + 26), "금천미트 가입 시", font=_font(20, bold=True), fill=muted)
    prefix = "‘영업사원 소개’에 "
    prefix_font = _font(27, bold=True)
    draw.text((102, hook_top + 59), prefix, font=prefix_font, fill=ink)
    prefix_width = draw.textbbox((0, 0), prefix, font=prefix_font)[2]
    draw.text((102 + prefix_width, hook_top + 59), "권오현", font=_font(29, bold=True), fill=gold)
    name_width = draw.textbbox((0, 0), "권오현", font=_font(29, bold=True))[2]
    draw.text(
        (102 + prefix_width + name_width, hook_top + 59),
        "을 입력해 주세요.",
        font=prefix_font,
        fill=ink,
    )
    draw.text(
        (102, hook_top + 108),
        "실시간 시세·원육 활용 정보와 메뉴에 맞는 1:1 상담을 무료로 제공합니다.",
        font=_font(20),
        fill=dark_green,
    )

    # 도메인은 실제 연결이 확인될 때까지 표시하지 않는다.
    draw.text((540, 1310), "도토리다판다", font=_font(18, bold=True), fill=muted, anchor="mm")

    output = BytesIO()
    canvas.save(output, format="PNG", optimize=True)
    return output.getvalue()
