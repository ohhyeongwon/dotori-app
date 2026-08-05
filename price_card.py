"""실시간 가격 결과를 공유용 4:5 PNG 단가표로 생성한다."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from functools import lru_cache
from io import BytesIO
from pathlib import Path
import re
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
FINAL_DESIGN_REFERENCE_PATH = ASSET_DIR / "design" / "market-report-final-reference.png"
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
    if scale > 1 and FINAL_DESIGN_REFERENCE_PATH.exists():
        with Image.open(FINAL_DESIGN_REFERENCE_PATH) as reference:
            branding = reference.convert("RGB").crop((225, 8, 560, 72))
        target_width = 470
        target_height = round(branding.height * target_width / branding.width)
        left = (canvas.width - target_width) // 2
        _paste_contained(canvas, branding, (left, 8, left + target_width, 8 + target_height))
        return {"approved_branding_output_size": (target_width, target_height)}

    logo_height = 104 if scale > 1 else 58
    logo_top = 10 if scale > 1 else 20
    dongwon = _load_official_logo(str(DONGWON_LOGO_PATH))
    geumcheon = _load_official_logo(str(GEUMCHEON_LOGO_PATH))
    dongwon_width = round(dongwon.width * logo_height / dongwon.height)
    geumcheon_width = round(geumcheon.width * logo_height / geumcheon.height)
    rail_width = dongwon_width + geumcheon_width + (92 if scale > 1 else 68)
    rail_left = (canvas.width - rail_width) // 2
    _paste_contained(
        canvas, dongwon,
        (rail_left, logo_top, rail_left + dongwon_width, logo_top + logo_height),
    )
    separator_x = rail_left + dongwon_width + (31 if scale > 1 else 23)
    draw.text(
        (separator_x, logo_top + logo_height / 2), "×",
        font=_font(34 if scale > 1 else 25), fill="#101713", anchor="mm",
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


def _paste_rounded_thumbnail(canvas, image, box, radius=10):
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


DISPLAY_ITEM_NAMES = {
    "imported_beef_intercostal": "소갈비살(늑간)",
    "imported_beef_back_rib": "빽립(갈비탕)",
}

REPORT_GROUP_STYLE = {
    "hanwoo": ("#74371f", "Korean Beef"),
    "beef_cattle": ("#a85a10", "Korean Young Beef"),
    "handon": ("#b91622", "Korean Pork"),
    "imported_beef": ("#123d7a", "Imported Beef"),
    "imported_pork": ("#087b7b", "Imported Pork"),
    "chicken": ("#3e7628", "Chicken"),
    "sliced_meat": ("#7b092b", "Sliced Meat"),
}

REPORT_PRICE_COLOR = {
    "hanwoo": "#c81620",
    "beef_cattle": "#c81620",
    "handon": "#c81620",
    "imported_beef": "#153887",
    "imported_pork": "#153887",
    "chicken": "#17231d",
    "sliced_meat": "#c81620",
}


def _display_item_name(item):
    return DISPLAY_ITEM_NAMES.get(item.get("item_id"), item["item_name"])


def _item_meta(item, category_id=""):
    storage = item.get("storage_status") or "보관 상태 확인 전"
    grade = f'{item["grade"]}등급' if item.get("grade") else ""
    if category_id in {"hanwoo", "beef_cattle"}:
        values = [storage, grade]
    elif category_id == "handon":
        values = [item.get("brand") or ""]
    elif category_id == "chicken":
        values = [item.get("brand") or ""]
    else:
        values = [item.get("origin") or "원산지 확인 전", storage]
    return " · ".join(value for value in values if value)


def _sliced_item_meta(item):
    origin = item.get("origin") or "원산지 확인 전"
    if origin not in {"원산지 확인 전"} and not origin.endswith("산"):
        origin = f"{origin}산"
    goods_name = str(item.get("goods_name") or "")
    thickness = re.search(r"\d+(?:\.\d+)?\s*mm", goods_name, flags=re.IGNORECASE)
    return " · ".join(value for value in [origin, thickness.group(0) if thickness else ""] if value)


def _draw_report_group(canvas, draw, group, box, row_height, product_images, compact=False):
    """카테고리 고유 색상과 품목 상태를 갖는 리포트 패널을 그린다."""
    if group.get("category_id") == "sliced_meat":
        return _draw_sliced_report_group(canvas, draw, group, box, compact=compact)
    left, top, right, bottom = box
    dark_green = "#123c2e"
    gold = "#a57a2c"
    ink = "#17231d"
    muted = "#777c78"
    header_color, english_name = REPORT_GROUP_STYLE.get(
        group.get("category_id"), (group.get("report_color") or dark_green, "")
    )
    header_height = 72 if compact else 84
    draw.rounded_rectangle(
        (left + 4, top + 7, right + 4, bottom + 7), radius=28, fill="#e7dfd2",
    )
    draw.rounded_rectangle(box, radius=28, fill="#fffdf9", outline="#d9d1c2", width=2)
    draw.rounded_rectangle(
        (left, top, right, top + header_height), radius=28, fill=header_color,
    )
    draw.rectangle((left, top + header_height - 28, right, top + header_height), fill=header_color)
    _draw_category_icon(draw, (left + 44, top + header_height / 2), header_color)
    draw.text(
        (left + 82, top + header_height / 2), group["category_name"],
        font=_font(29 if compact else 36, bold=True), fill="#ffffff", anchor="lm",
    )
    if english_name:
        draw.text(
            (right - 22, top + header_height / 2), english_name,
            font=_font(18 if compact else 23), fill="#fff7e8", anchor="rm",
        )

    for index, item in enumerate(group["items"]):
        row_top = top + header_height + index * row_height
        row_center = row_top + row_height / 2
        if index:
            draw.line((left + 24, row_top, right - 24, row_top), fill="#ece7de", width=2)
        image = product_images.get(item.get("image_url"))
        thumbnail_size = 140 if compact else 156
        content_left = left + 24
        if image is not None:
            thumb_top = row_center - thumbnail_size / 2
            _paste_rounded_thumbnail(
                canvas, image,
                (content_left, thumb_top, content_left + thumbnail_size, thumb_top + thumbnail_size),
                radius=10,
            )
            content_left += thumbnail_size + (16 if compact else 20)
        price_right = (
            min(right - 26, left + 1040)
            if compact and group.get("category_id") == "sliced_meat"
            else right - 24
        )
        price_reserve = 260 if compact else 340
        name_max_width = max(price_right - content_left - price_reserve, 105)
        display_name = _display_item_name(item)
        item_font = _fit_text(
            draw, display_name, name_max_width,
            start_size=38 if compact else 44, min_size=25 if compact else 30, bold=True,
        )
        draw.text(
            (content_left, row_center - (18 if compact else 23)), display_name,
            font=item_font, fill=ink, anchor="lm",
        )
        meta = _item_meta(item, group.get("category_id", ""))
        meta_font = _fit_text(
            draw, meta, max(name_max_width, 80),
            start_size=15 if compact else 18, min_size=11 if compact else 14,
        )
        draw.text(
            (content_left, row_center + (29 if compact else 35)), meta,
            font=meta_font, fill=muted, anchor="lm",
        )
        if item.get("kg_price") is not None:
            value = f'{item["kg_price"]:,.0f}원/kg'
            value_font = _fit_text(
                draw, value, price_reserve - 8,
                start_size=52 if compact else 58,
                min_size=38 if compact else 44,
                bold=True,
            )
            value_color = REPORT_PRICE_COLOR.get(group.get("category_id"), dark_green)
        else:
            value = item.get("display_status") or "현재 조회 불가"
            value_font = _font(19 if compact else 25, bold=True)
            value_color = gold if value == "연동 준비 중" else muted
        draw.text((price_right, row_center), value, font=value_font, fill=value_color, anchor="rm")


def _draw_sliced_report_group(canvas, draw, group, box, compact=False):
    """세절육은 사진 없이 같은 기준의 3열 가격 블록으로 조밀하게 표시한다."""
    left, top, right, bottom = box
    header_color, english_name = REPORT_GROUP_STYLE.get(
        group.get("category_id"), (group.get("report_color") or "#7b092b", "Sliced Meat")
    )
    header_height = 72 if compact else 84
    radius = 28
    draw.rounded_rectangle(
        (left + 4, top + 7, right + 4, bottom + 7), radius=radius, fill="#e7dfd2",
    )
    draw.rounded_rectangle(box, radius=radius, fill="#fffdf9", outline="#d9d1c2", width=2)
    draw.rounded_rectangle(
        (left, top, right, top + header_height), radius=radius, fill=header_color,
    )
    draw.rectangle((left, top + header_height - radius, right, top + header_height), fill=header_color)
    _draw_category_icon(draw, (left + 44, top + header_height / 2), header_color)
    draw.text(
        (left + 82, top + header_height / 2), group["category_name"],
        font=_font(29 if compact else 36, bold=True), fill="#ffffff", anchor="lm",
    )
    draw.text(
        (left + 230, top + header_height / 2), english_name,
        font=_font(18 if compact else 23), fill="#fff7e8", anchor="lm",
    )

    column_width = (right - left - 44) / 3
    content_top = top + header_height + (13 if compact else 24)
    for index, item in enumerate(group["items"]):
        column_left = left + 22 + index * column_width
        column_right = column_left + column_width
        if index:
            draw.line(
                (column_left - 10, content_top + 4, column_left - 10, bottom - 18),
                fill="#ece7de", width=2,
            )
        name = _display_item_name(item)
        name_font = _fit_text(
            draw, name, column_width - 22,
            start_size=34 if compact else 38,
            min_size=23 if compact else 27,
            bold=True,
        )
        draw.text((column_left, content_top), name, font=name_font, fill="#17231d")
        meta = _sliced_item_meta(item)
        meta_font = _fit_text(
            draw, meta, column_width - 22,
            start_size=16 if compact else 19,
            min_size=12 if compact else 15,
        )
        draw.text(
            (column_left, content_top + (40 if compact else 50)), meta,
            font=meta_font, fill="#777c78",
        )
        value = (
            f'{item["kg_price"]:,.0f}원/kg'
            if item.get("kg_price") is not None
            else item.get("display_status") or "현재 조회 불가"
        )
        value_font = _fit_text(
            draw, value, column_width - 22,
            start_size=48 if compact else 48,
            min_size=29 if compact else 34,
            bold=True,
        )
        draw.text(
            (column_left, content_top + (68 if compact else 96)), value,
            font=value_font, fill=REPORT_PRICE_COLOR.get(group.get("category_id"), "#123c2e"),
        )


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


def _draw_marketing_footer(canvas, draw, top, margin, width, height, kakao_chat_url):
    """네이버·가입 안내·앱·카카오 QR을 동적으로 구성한 종합 리포트 전용 영역."""
    left, right = margin, width - margin
    bottom = height - 54
    dark_green = "#123c2e"
    gold = "#a57a2c"
    ink = "#17231d"
    muted = "#68716b"
    draw.rounded_rectangle(
        (left + 5, top + 8, right + 5, bottom + 8), radius=30, fill="#e5ddcf",
    )
    draw.rounded_rectangle(
        (left, top, right, bottom), radius=30,
        fill="#fffaf1", outline="#d8cfbe", width=2,
    )
    inner_top = top + 28
    inner_bottom = bottom - 48
    total_width = right - left - 48
    nav_width = 275
    center_width = 440
    app_width = 285
    qr_width = total_width - nav_width - center_width - app_width
    x1 = left + 24
    x2 = x1 + nav_width
    x3 = x2 + center_width
    x4 = x3 + app_width

    for divider in (x2, x3, x4):
        draw.line((divider, inner_top + 12, divider, inner_bottom - 4), fill="#e7dfd2", width=2)

    # PC / NAVER 검색 경로
    draw.text((x1 + 16, inner_top + 8), "PC에서도 간편하게!", font=_font(19, bold=True), fill=dark_green)
    draw.text((x1 + 16, inner_top + 47), "NAVER", font=_font(35, bold=True), fill="#138a45")
    draw.text((x1 + 16, inner_top + 90), "네이버에서 금천미트 검색", font=_font(18), fill=ink)
    search_top = inner_top + 132
    draw.rounded_rectangle(
        (x1 + 16, search_top, x2 - 20, search_top + 56), radius=9,
        fill="#ffffff", outline="#74a98b", width=2,
    )
    draw.text((x1 + 31, search_top + 28), "금천미트", font=_font(19, bold=True), fill=ink, anchor="lm")
    draw.rectangle((x2 - 72, search_top, x2 - 20, search_top + 56), fill="#138a45")
    draw.ellipse((x2 - 58, search_top + 15, x2 - 39, search_top + 34), outline="#ffffff", width=3)
    draw.line((x2 - 42, search_top + 32, x2 - 32, search_top + 43), fill="#ffffff", width=3)

    # 가장 중요한 가입 전환 메시지
    center_x = x2 + 28
    draw.text((center_x, inner_top + 6), "금천미트 회원가입 시", font=_font(22, bold=True), fill=dark_green)
    draw.text((center_x, inner_top + 48), "영업사원 소개", font=_font(25, bold=True), fill=ink)
    draw.text((center_x, inner_top + 91), "권오현", font=_font(48, bold=True), fill=gold)
    name_width = draw.textbbox((0, 0), "권오현", font=_font(48, bold=True))[2]
    draw.text((center_x + name_width + 14, inner_top + 107), "입력", font=_font(28, bold=True), fill=ink)
    draw.text(
        (center_x, inner_top + 159), "실시간 시세 · 원육 상담 · 메뉴 컨설팅",
        font=_font(18), fill=dark_green,
    )
    draw.text((center_x, inner_top + 196), "무료 제공", font=_font(20, bold=True), fill=dark_green)
    draw.text((center_x, inner_top + 238), f"☎ {CONTACT_PHONE}", font=_font(27, bold=True), fill=ink)

    # 원본 스마트폰 자산이 없으므로 단정한 앱 설치 UI로 구성
    app_left = x3 + 25
    draw.text((app_left, inner_top + 8), "앱에서도 편리하게!", font=_font(19, bold=True), fill=dark_green)
    phone_box = (app_left + 32, inner_top + 48, x4 - 42, inner_top + 230)
    draw.rounded_rectangle(phone_box, radius=24, fill="#ffffff", outline="#b9b7af", width=3)
    draw.rounded_rectangle(
        (phone_box[0] + 16, phone_box[1] + 28, phone_box[2] - 16, phone_box[1] + 78),
        radius=11, fill="#5b201d",
    )
    draw.text(
        ((phone_box[0] + phone_box[2]) / 2, phone_box[1] + 53), "금천미트",
        font=_font(18, bold=True), fill="#ffffff", anchor="mm",
    )
    draw.text(
        ((phone_box[0] + phone_box[2]) / 2, phone_box[1] + 111), "Google Play",
        font=_font(18, bold=True), fill=ink, anchor="mm",
    )
    draw.text(
        ((phone_box[0] + phone_box[2]) / 2, phone_box[1] + 145), "금천미트 다운로드",
        font=_font(15), fill=muted, anchor="mm",
    )

    # 현재 랜딩페이지와 동일한 카카오 URL만 QR에 사용
    qr = _create_qr_image(kakao_chat_url, 144)
    qr_center = (x4 + right) / 2
    draw.text((qr_center, inner_top + 8), "카카오톡 상담", font=_font(20, bold=True), fill=dark_green, anchor="ma")
    if qr is not None:
        canvas.paste(qr, (round(qr_center - 72), inner_top + 49))
    draw.text((qr_center, inner_top + 205), "1:1 상담", font=_font(19, bold=True), fill=ink, anchor="ma")
    draw.text((qr_center, inner_top + 238), "바로 연결", font=_font(16), fill=muted, anchor="ma")

    benefit_top = top + 348
    draw.rounded_rectangle(
        (x2 + 28, benefit_top, x4 - 28, benefit_top + 72), radius=16,
        fill="#f0f3ed", outline="#d5ddd4", width=1,
    )
    draw.text(
        ((x2 + x4) / 2, benefit_top + 36),
        "권오현 입력 고객 전용  ·  실시간 시세  ·  원육 상담  ·  메뉴 컨설팅 무료 제공",
        font=_font(18, bold=True), fill=dark_green, anchor="mm",
    )

    disclaimer = "※ 본 단가는 금천미트 온라인 최저가 기준이며, 시장 상황에 따라 변동될 수 있습니다."
    draw.text((width / 2, bottom - 27), disclaimer, font=_font(17), fill=muted, anchor="mm")


@lru_cache(maxsize=1)
def _load_approved_portrait():
    """승인 기준 이미지에 포함된 권오현 인물 영역만 재사용한다."""
    if not FINAL_DESIGN_REFERENCE_PATH.exists():
        return None
    with Image.open(FINAL_DESIGN_REFERENCE_PATH) as image:
        image.load()
        # 기준 이미지(1024×1536) 하단 배너의 인물 영역.
        return image.convert("RGB").crop((132, 1227, 438, 1503))


@lru_cache(maxsize=1)
def _load_approved_footer_banner():
    """승인 기준 이미지의 하단 홍보 배너를 비율 그대로 불러온다."""
    if not FINAL_DESIGN_REFERENCE_PATH.exists():
        return None
    with Image.open(FINAL_DESIGN_REFERENCE_PATH) as image:
        image.load()
        return image.convert("RGB").crop((10, 1228, 1015, 1503))


def _draw_reference_marketing_footer(canvas, draw, top, margin, width, height, kakao_chat_url):
    """승인본의 시선 흐름을 좌표 기반으로 재현한 종합 단가표 배너."""
    left, right = margin, width - margin
    disclaimer_y = height - 35
    bottom = disclaimer_y - 34
    radius = 28

    # 승인본의 인물·네이버·스마트폰 시선 흐름은 배너 원본을 그대로 보존한다.
    approved_banner = _load_approved_footer_banner()
    if approved_banner is not None:
        target_width = int(right - left)
        target_height = round(target_width * approved_banner.height / approved_banner.width)
        fitted = approved_banner.resize((target_width, target_height), Image.Resampling.LANCZOS)
        banner_top = int(top + max((bottom - top - target_height) / 2, 0))
        mask = Image.new("L", fitted.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle(
            (0, 0, fitted.width - 1, fitted.height - 1), radius=radius, fill=255,
        )
        canvas.paste(fitted, (int(left), banner_top), mask)
        draw.rounded_rectangle(
            (left, banner_top, right, banner_top + target_height),
            radius=radius, outline="#9bcfc2", width=2,
        )

        # 기준 이미지 QR 위치에 현재 랜딩페이지와 동일한 URL의 QR을 다시 그린다.
        qr_size = round(target_width * 112 / 1005)
        qr_left = int(left + target_width * 885 / 1005)
        qr_top = int(banner_top + target_height * 105 / 275)
        qr = _create_qr_image(kakao_chat_url, qr_size)
        if qr is not None:
            canvas.paste(qr, (qr_left, qr_top))
        disclaimer = "※ 본 단가는 금천미트 온라인 최저가 기준이며, 시장 상황에 따라 변동될 수 있습니다."
        draw.text((width / 2, disclaimer_y), disclaimer, font=_font(18), fill="#68716b", anchor="mm")
        return

    # 승인본과 같은 민트-화이트-민트 가로 배너.
    banner = Image.new("RGB", (int(right - left), int(bottom - top)), "#eefcf7")
    banner_draw = ImageDraw.Draw(banner)
    for x in range(banner.width):
        center_distance = abs(x - banner.width / 2) / (banner.width / 2)
        mint = int(236 - 42 * center_distance)
        banner_draw.line((x, 0, x, banner.height), fill=(mint, 250, 243))
    mask = Image.new("L", banner.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, banner.width - 1, banner.height - 1), radius=radius, fill=255)
    canvas.paste(banner, (int(left), int(top)), mask)
    draw.rounded_rectangle((left, top, right, bottom), radius=radius, outline="#9bcfc2", width=2)

    banner_h = bottom - top
    nav_left, nav_right = left + 26, left + 300
    portrait_left, portrait_right = left + 210, left + 575
    center_left, center_right = left + 565, left + 955
    phone_left, phone_right = left + 955, left + 1212
    qr_left, qr_right = left + 1210, right - 18

    # NAVER 검색 UI
    draw.text((nav_left + 12, top + 28), "PC에서도 간편하게!", font=_font(19, bold=True), fill="#123c2e")
    monitor = (nav_left, top + 75, nav_right, bottom - 52)
    draw.rounded_rectangle(monitor, radius=16, fill="#263b39", outline="#ffffff", width=4)
    draw.rounded_rectangle((monitor[0] + 16, monitor[1] + 17, monitor[2] - 16, monitor[3] - 20), radius=8, fill="#ffffff")
    draw.text(((nav_left + nav_right) / 2, top + 135), "NAVER", font=_font(37, bold=True), fill="#0aa63d", anchor="mm")
    search = (nav_left + 28, top + 170, nav_right - 28, top + 226)
    draw.rounded_rectangle(search, radius=8, fill="#ffffff", outline="#0aa63d", width=3)
    draw.text((search[0] + 16, (search[1] + search[3]) / 2), "금천미트", font=_font(19, bold=True), fill="#17231d", anchor="lm")
    draw.rectangle((search[2] - 48, search[1], search[2], search[3]), fill="#0aa63d")
    draw.ellipse((search[2] - 35, search[1] + 13, search[2] - 17, search[1] + 31), outline="#ffffff", width=3)
    draw.line((search[2] - 20, search[1] + 29, search[2] - 10, search[1] + 40), fill="#ffffff", width=3)

    # 승인본 인물 이미지
    portrait = _load_approved_portrait()
    if portrait is not None:
        fitted = ImageOps.contain(portrait, (portrait_right - portrait_left, int(banner_h - 16)), Image.Resampling.LANCZOS)
        canvas.paste(fitted, (int(portrait_left), int(bottom - fitted.height - 2)))

    # 중앙 가입 메시지
    center_x = (center_left + center_right) / 2
    draw.rounded_rectangle((center_left + 20, top + 18, center_right - 20, top + 67), radius=24, fill="#e65d0a")
    draw.text((center_x, top + 43), "금천미트 회원가입 시", font=_font(23, bold=True), fill="#ffffff", anchor="mm")
    draw.text((center_x, top + 91), "영업사원 소개", font=_font(29, bold=True), fill="#123c2e", anchor="mm")
    draw.text((center_x - 12, top + 157), "권오현", font=_font(60, bold=True), fill="#0c3042", anchor="mm")
    draw.text((center_right - 18, top + 164), "입력!", font=_font(32, bold=True), fill="#0c3042", anchor="rm")
    badges = ["실시간 시세", "원육 상담", "메뉴 컨설팅"]
    badge_w = 108
    badge_gap = 8
    badges_left = center_x - (badge_w * 3 + badge_gap * 2) / 2
    for index, label in enumerate(badges):
        x = badges_left + index * (badge_w + badge_gap)
        draw.rounded_rectangle((x, top + 205, x + badge_w, top + 242), radius=18, fill="#0d4765")
        draw.text((x + badge_w / 2, top + 224), f"✓ {label}", font=_font(14, bold=True), fill="#ffffff", anchor="mm")
    draw.text((center_x, top + 271), "무료 제공!", font=_font(28, bold=True), fill="#123c2e", anchor="mm")
    draw.rounded_rectangle((center_left + 36, top + 300, center_right - 36, top + 352), radius=24, fill="#ffffff", outline="#0aa36b", width=3)
    draw.text((center_x, top + 326), f"☎ {CONTACT_PHONE}", font=_font(29, bold=True), fill="#08724f", anchor="mm")

    # 스마트폰 / Google Play UI
    draw.text(((phone_left + phone_right) / 2, top + 28), "앱에서도 편리하게!", font=_font(19, bold=True), fill="#123c2e", anchor="mm")
    phone = (phone_left + 46, top + 63, phone_right - 25, bottom - 18)
    draw.rounded_rectangle(phone, radius=26, fill="#162322", outline="#ffffff", width=4)
    screen = (phone[0] + 13, phone[1] + 22, phone[2] - 13, phone[3] - 18)
    draw.rounded_rectangle(screen, radius=15, fill="#ffffff")
    draw.text(((screen[0] + screen[2]) / 2, screen[1] + 36), "▶ Google Play", font=_font(18, bold=True), fill="#17231d", anchor="mm")
    draw.rounded_rectangle((screen[0] + 16, screen[1] + 67, screen[2] - 16, screen[1] + 117), radius=10, fill="#74221f")
    draw.text(((screen[0] + screen[2]) / 2, screen[1] + 92), "금천미트", font=_font(18, bold=True), fill="#ffffff", anchor="mm")
    for row in range(3):
        y = screen[1] + 142 + row * 47
        draw.rounded_rectangle((screen[0] + 16, y, screen[2] - 16, y + 34), radius=6, fill="#eef2ee")

    # 실제 랜딩페이지 카카오톡 URL QR
    draw.rounded_rectangle((qr_left, top + 78, qr_right, bottom - 18), radius=18, fill="#ffe812", outline="#e0c800", width=2)
    qr = _create_qr_image(kakao_chat_url, 132)
    if qr is not None:
        canvas.paste(qr, (int((qr_left + qr_right - 132) / 2), int(top + 104)))
    draw.text(((qr_left + qr_right) / 2, top + 256), "카카오톡 1:1 상담", font=_font(18, bold=True), fill="#2c2300", anchor="mm")
    draw.text(((qr_left + qr_right) / 2, top + 286), "바로 연결!", font=_font(16, bold=True), fill="#2c2300", anchor="mm")

    disclaimer = "※ 본 단가는 금천미트 온라인 최저가 기준이며, 시장 상황에 따라 변동될 수 있습니다."
    draw.text((width / 2, disclaimer_y), disclaimer, font=_font(18), fill="#68716b", anchor="mm")


def create_market_report_png(
    title, groups, queried_at=None, canvas_size=OVERALL_REPORT_SIZE, kakao_chat_url="",
):
    """제목·카테고리·품목·가격을 받아 공유용 범용 축산 단가표 PNG를 만든다."""
    queried_at = queried_at or datetime.now(ZoneInfo("Asia/Seoul"))
    width, height = canvas_size
    if canvas_size not in (OVERALL_REPORT_SIZE, CATEGORY_REPORT_SIZE):
        raise ValueError("지원하는 단가표 크기는 1440×2560 또는 1080×1350입니다.")

    canvas = Image.new("RGB", canvas_size, "#f7f8f7")
    draw = ImageDraw.Draw(canvas)
    dark_green = "#123c2e"
    gold = "#a57a2c"
    ink = "#17231d"
    muted = "#68716b"
    scale = width / 1080
    margin = 28 if canvas_size == OVERALL_REPORT_SIZE else 54
    if canvas_size != OVERALL_REPORT_SIZE:
        _draw_paper_texture(draw, height=height, width=width)
    _draw_official_branding(canvas, draw, margin, scale)
    title_font = _fit_text(
        draw, title, width - margin * 2 - 80,
        start_size=104 if scale > 1 else 66, min_size=78 if scale > 1 else 48, bold=True,
    )
    draw.text((width / 2, 128 if scale > 1 else 104), title, font=title_font, fill=dark_green, anchor="ma")
    draw.text(
        (width - margin, 35 if scale > 1 else 188), queried_at.strftime("%Y.%m.%d %H:%M 기준"),
        font=_font(23 if scale > 1 else 21, bold=True), fill=ink, anchor="ra",
    )
    draw.text(
        (width / 2, 260 if scale > 1 else 230), "주요 축산물의 현재 최저가를 한눈에 확인하세요!",
        font=_font(25 if scale > 1 else 20, bold=True), fill=ink, anchor="ma",
    )
    header_line_y = 314 if scale > 1 else 286
    draw.line((margin, header_line_y, width - margin, header_line_y), fill="#d8cfbc", width=2)

    product_images = _prepare_report_images(groups)
    if canvas_size == OVERALL_REPORT_SIZE:
        y = 326
        gap = 14
        column_gap = 18
        card_width = (width - margin * 2 - column_gap) / 2
        pairs = [(0, 1), (2, 3), (4, 5)]
        for first_index, second_index in pairs:
            pair = [groups[index] for index in (first_index, second_index) if index < len(groups)]
            if not pair:
                continue
            item_count = max(len(group["items"]) for group in pair)
            box_height = 72 + item_count * 152
            for column, group in enumerate(pair):
                left = margin + column * (card_width + column_gap)
                _draw_report_group(
                    canvas, draw, group, (left, y, left + card_width, y + box_height),
                    152, product_images, compact=True,
                )
            y += box_height + gap
        for group in groups[6:]:
            box_height = 72 + 154
            _draw_report_group(
                canvas, draw, group, (margin, y, width - margin, y + box_height),
                100, product_images, compact=True,
            )
            y += box_height + gap
        footer_top = max(y + 10, 1970)
    else:
        group = groups[0]
        row_height = 132
        box_height = (
            84 + 190 if group.get("category_id") == "sliced_meat"
            else 84 + len(group["items"]) * row_height
        )
        _draw_report_group(
            canvas, draw, group, (72, 314, 1008, 314 + box_height),
            row_height, product_images,
        )
        draw.text((72, 866), "표시 기준", font=_font(19, bold=True), fill=dark_green)
        draw.text(
            (72, 902), "연결된 품목은 원/kg 가격을, 미연결 품목은 연동 상태를 표시합니다.",
            font=_font(18), fill=muted,
        )
        footer_top = 946

    if canvas_size == OVERALL_REPORT_SIZE:
        _draw_reference_marketing_footer(
            canvas, draw, footer_top, margin, width, height, kakao_chat_url,
        )
    else:
        _draw_report_footer(
            canvas, draw, footer_top, margin, width, height, scale, kakao_chat_url,
        )

    output = BytesIO()
    canvas.save(output, format="PNG", optimize=True)
    return output.getvalue()
