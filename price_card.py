"""실시간 가격 결과를 공유용 4:5 PNG 단가표로 생성한다."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from functools import lru_cache
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

import requests
from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageOps


WIDTH = 1080
HEIGHT = 1350
OVERALL_REPORT_SIZE = (1440, 2560)
CATEGORY_REPORT_SIZE = (1080, 1350)
ASSET_DIR = Path(__file__).resolve().parent / "assets"
DONGWON_LOGO_PATH = ASSET_DIR / "logos" / "dongwon-group-official.png"
GEUMCHEON_LOGO_PATH = ASSET_DIR / "logos" / "geumcheon-meat-official.png"
REPORT_IMAGE_TIMEOUT_SECONDS = 8
CONTACT_PHONE = "010-6503-8953"


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


def _draw_paper_texture(draw, height=HEIGHT, width=WIDTH):
    """가독성을 해치지 않는 미세한 한지 결을 직접 그린다."""
    for y in range(18, height, 31):
        offset = (y * 7) % 29
        for x in range(offset, width, 47):
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


def _draw_report_motif(draw, width):
    """사진 대신 직접 그린 절제된 축산 라인 모티프를 배치한다."""
    right = width - 82
    left = right - 255
    draw.ellipse((left, 52, right, 288), fill="#eadbd2", outline="#d8bdad", width=3)
    draw.ellipse((left + 36, 84, right - 28, 258), fill="#f3e8df")
    draw.arc((left + 50, 98, right - 34, 242), 205, 344, fill="#c7a080", width=5)
    draw.line((left + 88, 105, right - 80, 236), fill="#d3b5a5", width=4)
    draw.line((left + 48, 190, right - 42, 132), fill="#b18b49", width=4)


def _crop_white_margin(image):
    """원본 색상은 유지하고 바깥쪽 흰 여백만 계산해 제거한다."""
    rgba = image.convert("RGBA")
    white = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
    difference = ImageChops.difference(rgba, white).convert("L")
    bbox = difference.point(lambda value: 255 if value > 10 else 0).getbbox()
    return rgba.crop(bbox) if bbox else rgba


@lru_cache(maxsize=2)
def _load_official_logo(path_text):
    with Image.open(path_text) as image:
        image.load()
        return image.convert("RGBA")


def _paste_contained(canvas, image, box, background="#ffffff"):
    """이미지 비율을 유지한 채 지정 영역 중앙에 배치한다."""
    left, top, right, bottom = [int(value) for value in box]
    target_size = (max(right - left, 1), max(bottom - top, 1))
    fitted = ImageOps.contain(image.convert("RGBA"), target_size, Image.Resampling.LANCZOS)
    plate = Image.new("RGBA", target_size, background)
    plate.alpha_composite(
        fitted,
        ((target_size[0] - fitted.width) // 2, (target_size[1] - fitted.height) // 2),
    )
    canvas.paste(plate.convert("RGB"), (left, top))
    return fitted.size


def _draw_official_branding(canvas, draw, margin, scale):
    """사용자가 제공한 두 공식 로고만 원본 비율로 배치한다."""
    logo_height = 58 if scale > 1 else 44
    logo_top = 40 if scale > 1 else 32
    dongwon = _load_official_logo(str(DONGWON_LOGO_PATH))
    geumcheon = _load_official_logo(str(GEUMCHEON_LOGO_PATH))
    dongwon_width = round(dongwon.width * logo_height / dongwon.height)
    geumcheon_width = round(geumcheon.width * logo_height / geumcheon.height)
    rail_width = dongwon_width + geumcheon_width + (84 if scale > 1 else 64)
    rail_height = logo_height + (20 if scale > 1 else 16)
    draw.rounded_rectangle(
        (margin, logo_top - 10, margin + rail_width, logo_top - 10 + rail_height),
        radius=12, fill="#ffffff", outline="#e6e1d7", width=1,
    )
    _paste_contained(
        canvas, dongwon,
        (margin + 10, logo_top, margin + 10 + dongwon_width, logo_top + logo_height),
    )
    separator_x = margin + 10 + dongwon_width + (26 if scale > 1 else 20)
    draw.text(
        (separator_x, logo_top + logo_height / 2), "×",
        font=_font(22 if scale > 1 else 17), fill="#8b8f8b", anchor="mm",
    )
    geumcheon_left = separator_x + (28 if scale > 1 else 22)
    _paste_contained(
        canvas, geumcheon,
        (geumcheon_left, logo_top, geumcheon_left + geumcheon_width, logo_top + logo_height),
    )
    return {
        "dongwon_output_size": (dongwon_width, logo_height),
        "geumcheon_output_size": (geumcheon_width, logo_height),
    }


@lru_cache(maxsize=128)
def _fetch_product_image_bytes(image_url):
    parsed = urlparse(image_url)
    if parsed.scheme != "https" or parsed.hostname != "static.ekcm.co.kr":
        return b""
    try:
        response = requests.get(image_url, timeout=REPORT_IMAGE_TIMEOUT_SECONDS)
        response.raise_for_status()
        if not response.headers.get("content-type", "").lower().startswith("image/"):
            return b""
        return response.content
    except requests.RequestException:
        return b""


def _load_product_image(image_url):
    content = _fetch_product_image_bytes(image_url)
    if not content:
        return None
    try:
        with Image.open(BytesIO(content)) as image:
            image.load()
            return image.convert("RGB")
    except (OSError, ValueError):
        return None


def _prepare_report_images(groups):
    urls = {
        item.get("image_url")
        for group in groups for item in group["items"]
        if item.get("image_status") == "연결" and item.get("image_url")
    }
    images = {}
    if not urls:
        return images
    with ThreadPoolExecutor(max_workers=min(12, len(urls))) as executor:
        futures = {executor.submit(_load_product_image, url): url for url in urls}
        for future in as_completed(futures):
            url = futures[future]
            try:
                image = future.result()
            except Exception:
                image = None
            if image is not None:
                images[url] = image
    return images


def _paste_rounded_thumbnail(canvas, image, box, radius=9):
    left, top, right, bottom = [int(value) for value in box]
    size = (right - left, bottom - top)
    plate = Image.new("RGB", size, "#f5f3ee")
    fitted = ImageOps.contain(image.convert("RGB"), size, Image.Resampling.LANCZOS)
    plate.paste(fitted, ((size[0] - fitted.width) // 2, (size[1] - fitted.height) // 2))
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (0, 0, size[0] - 1, size[1] - 1), radius=radius, fill=255,
    )
    canvas.paste(plate, (left, top), mask)
    ImageDraw.Draw(canvas).rounded_rectangle(
        (left, top, right, bottom), radius=radius, outline="#ded8cc", width=1,
    )


def _draw_category_icon(draw, center, color):
    """정확한 상품 사진이 없을 때 사용하는 비상품성 컬러 아이콘."""
    x, y = center
    draw.ellipse((x - 25, y - 25, x + 25, y + 25), outline="#ffffff", width=3)
    draw.arc((x - 15, y - 12, x + 14, y + 13), 30, 235, fill="#ffffff", width=3)
    draw.line((x - 13, y + 9, x + 13, y - 8), fill="#ffffff", width=3)


def _item_meta(item):
    values = [
        item.get("origin") or "원산지 확인 전",
        item.get("storage_status") or "보관 상태 확인 전",
        item.get("brand") or "",
        f'{item["grade"]}등급' if item.get("grade") else "",
    ]
    return " · ".join(value for value in values if value)


def _draw_report_group(canvas, draw, group, box, row_height, product_images, compact=False):
    """카테고리 고유 색상과 품목 상태를 갖는 리포트 패널을 그린다."""
    left, top, right, bottom = box
    dark_green = "#123c2e"
    gold = "#a57a2c"
    ink = "#17231d"
    muted = "#777c78"
    header_color = group.get("report_color") or dark_green
    header_height = 78 if compact else 88
    draw.rounded_rectangle(
        (left + 3, top + 5, right + 3, bottom + 5), radius=24, fill="#e8e1d5",
    )
    draw.rounded_rectangle(box, radius=24, fill="#fffdf9", outline="#d9d1c2", width=2)
    draw.rounded_rectangle(
        (left, top, right, top + header_height), radius=24, fill=header_color,
    )
    draw.rectangle((left, top + header_height - 24, right, top + header_height), fill=header_color)
    _draw_category_icon(draw, (left + 48, top + header_height / 2), header_color)
    draw.text(
        (left + 88, top + header_height / 2), group["category_name"],
        font=_font(27 if compact else 34, bold=True), fill="#ffffff", anchor="lm",
    )

    for index, item in enumerate(group["items"]):
        row_top = top + header_height + index * row_height
        row_center = row_top + row_height / 2
        if index:
            draw.line((left + 24, row_top, right - 24, row_top), fill="#ece7de", width=2)
        image = product_images.get(item.get("image_url"))
        thumbnail_size = 66 if compact else 86
        content_left = left + 28
        if image is not None:
            thumb_top = row_center - thumbnail_size / 2
            _paste_rounded_thumbnail(
                canvas, image,
                (content_left, thumb_top, content_left + thumbnail_size, thumb_top + thumbnail_size),
                radius=9,
            )
            content_left += thumbnail_size + (16 if compact else 20)
        name_max_width = right - content_left - (220 if compact else 300)
        item_font = _fit_text(
            draw, item["item_name"], name_max_width,
            start_size=27 if compact else 34, min_size=20 if compact else 25, bold=True,
        )
        draw.text(
            (content_left, row_center - (14 if compact else 18)), item["item_name"],
            font=item_font, fill=ink, anchor="lm",
        )
        meta = _item_meta(item)
        meta_font = _fit_text(
            draw, meta, max(name_max_width, 80),
            start_size=15 if compact else 19, min_size=12 if compact else 15,
        )
        draw.text(
            (content_left, row_center + (23 if compact else 30)), meta,
            font=meta_font, fill=muted, anchor="lm",
        )
        if item.get("kg_price") is not None:
            value = f'{item["kg_price"]:,.0f}원/kg'
            value_font = _font(32 if compact else 42, bold=True)
            value_color = dark_green
        else:
            value = item.get("display_status") or "현재 조회 불가"
            value_font = _font(19 if compact else 25, bold=True)
            value_color = gold if value == "연동 준비 중" else muted
        draw.text((right - 28, row_center), value, font=value_font, fill=value_color, anchor="rm")


def _create_qr_image(url, size):
    if not url:
        return None
    try:
        import qrcode

        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=6,
            border=2,
        )
        qr.add_data(url)
        qr.make(fit=True)
        image = qr.make_image(fill_color="#123c2e", back_color="white").convert("RGB")
        return image.resize((size, size), Image.Resampling.NEAREST)
    except (ImportError, ValueError):
        return None


def _draw_report_footer(canvas, draw, top, margin, width, height, scale, kakao_chat_url):
    dark_green = "#123c2e"
    gold = "#a57a2c"
    ink = "#17231d"
    muted = "#68716b"
    bottom = min(
        height - (90 if scale > 1 else 72),
        top + (270 if scale > 1 else 235),
    )
    draw.rounded_rectangle(
        (margin, top, width - margin, bottom), radius=22,
        fill="#f0f2ed", outline="#cbd2ca", width=2,
    )
    draw.rectangle((margin, top + 20, margin + 6, bottom - 20), fill=gold)
    text_x = margin + (38 if scale > 1 else 30)
    draw.text(
        (text_x, top + 24), "금천미트 가입 시",
        font=_font(22 if scale > 1 else 18, bold=True), fill=muted,
    )
    line_y = top + (69 if scale > 1 else 57)
    prefix = "영업사원 소개에 "
    prefix_font = _font(27 if scale > 1 else 22, bold=True)
    draw.text((text_x, line_y), prefix, font=prefix_font, fill=ink)
    prefix_width = draw.textbbox((0, 0), prefix, font=prefix_font)[2]
    name_font = _font(31 if scale > 1 else 25, bold=True)
    draw.text((text_x + prefix_width, line_y), "권오현", font=name_font, fill=gold)
    name_width = draw.textbbox((0, 0), "권오현", font=name_font)[2]
    draw.text((text_x + prefix_width + name_width, line_y), " 입력", font=prefix_font, fill=ink)
    draw.text(
        (text_x, top + (126 if scale > 1 else 103)),
        "실시간 시세 · 원육 상담 · 메뉴 컨설팅 무료 제공",
        font=_font(22 if scale > 1 else 18), fill=dark_green,
    )
    draw.text(
        (text_x, top + (174 if scale > 1 else 142)), f"☎ {CONTACT_PHONE}",
        font=_font(29 if scale > 1 else 24, bold=True), fill=ink,
    )
    qr_size = 126 if scale > 1 else 100
    qr = _create_qr_image(kakao_chat_url, qr_size)
    if qr is not None:
        qr_left = width - margin - qr_size - (34 if scale > 1 else 26)
        qr_top = top + (24 if scale > 1 else 20)
        canvas.paste(qr, (qr_left, qr_top))
        draw.text(
            (qr_left + qr_size / 2, qr_top + qr_size + 9), "1:1 상담",
            font=_font(17 if scale > 1 else 14, bold=True), fill=dark_green, anchor="ma",
        )


def create_market_report_png(
    title, groups, queried_at=None, canvas_size=OVERALL_REPORT_SIZE, kakao_chat_url="",
):
    """제목·카테고리·품목·가격을 받아 공유용 범용 축산 단가표 PNG를 만든다."""
    queried_at = queried_at or datetime.now(ZoneInfo("Asia/Seoul"))
    width, height = canvas_size
    if canvas_size not in (OVERALL_REPORT_SIZE, CATEGORY_REPORT_SIZE):
        raise ValueError("지원하는 단가표 크기는 1440×2560 또는 1080×1350입니다.")

    canvas = Image.new("RGB", canvas_size, "#f7f3e9")
    draw = ImageDraw.Draw(canvas)
    dark_green = "#123c2e"
    gold = "#a57a2c"
    ink = "#17231d"
    muted = "#68716b"
    scale = width / 1080
    margin = 90 if canvas_size == OVERALL_REPORT_SIZE else 72
    _draw_paper_texture(draw, height=height, width=width)
    draw.rectangle((0, 0, int(18 * scale), height), fill=dark_green)
    draw.rectangle((int(18 * scale), 0, int(23 * scale), height), fill=gold)
    _draw_official_branding(canvas, draw, margin, scale)
    title_font = _fit_text(
        draw, title, width - margin * 2 - 280,
        start_size=68 if scale > 1 else 54, min_size=48 if scale > 1 else 42, bold=True,
    )
    draw.text((margin, 132 if scale > 1 else 108), title, font=title_font, fill=dark_green)
    draw.text(
        (margin, 225 if scale > 1 else 190), queried_at.strftime("%Y.%m.%d %H:%M 기준"),
        font=_font(29 if scale > 1 else 23), fill=muted,
    )
    draw.text(
        (margin, 280 if scale > 1 else 235), "주요 축산물의 현재 최저가를 한눈에 확인하세요.",
        font=_font(27 if scale > 1 else 22), fill=ink,
    )
    header_line_y = 350 if scale > 1 else 292
    draw.line((margin, header_line_y, width - margin, header_line_y), fill="#d8cfbc", width=2)

    product_images = _prepare_report_images(groups)
    if canvas_size == OVERALL_REPORT_SIZE:
        y = 390
        gap = 20
        card_width = 620
        column_gap = 20
        pairs = [(0, 1), (2, 3), (4, 5)]
        for first_index, second_index in pairs:
            pair = [groups[index] for index in (first_index, second_index) if index < len(groups)]
            if not pair:
                continue
            item_count = max(len(group["items"]) for group in pair)
            box_height = 96 + item_count * 105
            for column, group in enumerate(pair):
                left = margin + column * (card_width + column_gap)
                _draw_report_group(
                    canvas, draw, group, (left, y, left + card_width, y + box_height),
                    105, product_images, compact=True,
                )
            y += box_height + gap
        for group in groups[6:]:
            box_height = 96 + len(group["items"]) * 105
            _draw_report_group(
                canvas, draw, group, (margin, y, width - margin, y + box_height),
                105, product_images, compact=True,
            )
            y += box_height + gap
        footer_top = 2110
    else:
        group = groups[0]
        row_height = 140
        box_height = 108 + len(group["items"]) * row_height
        _draw_report_group(
            canvas, draw, group, (72, 330, 1008, 330 + box_height),
            row_height, product_images,
        )
        draw.text((72, 880), "표시 기준", font=_font(20, bold=True), fill=dark_green)
        draw.text(
            (72, 919), "연결된 품목은 원/kg 가격을, 미연결 품목은 연동 상태를 표시합니다.",
            font=_font(20), fill=muted,
        )
        footer_top = 960

    _draw_report_footer(
        canvas, draw, footer_top, margin, width, height, scale, kakao_chat_url,
    )

    output = BytesIO()
    canvas.save(output, format="PNG", optimize=True)
    return output.getvalue()
