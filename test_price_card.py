import unittest
from datetime import datetime
from io import BytesIO
from unittest.mock import patch
from zoneinfo import ZoneInfo

from PIL import Image

from price_card import (
    CATEGORY_REPORT_SIZE,
    OVERALL_REPORT_SIZE,
    create_market_report_png,
    create_price_card_png,
)


class PriceCardTest(unittest.TestCase):
    def test_generates_4_by_5_png(self):
        products = [
            {"label": "테스트 상품", "kg_price": 20300},
            {"label": "두 번째 상품", "kg_price": 26900},
        ]
        result = create_price_card_png(
            "육회",
            products,
            queried_at=datetime(2026, 8, 2, 10, 30, tzinfo=ZoneInfo("Asia/Seoul")),
        )
        image = Image.open(BytesIO(result))
        self.assertEqual(image.format, "PNG")
        self.assertEqual(image.size, (1080, 1350))
        self.assertGreater(len(result), 20_000)

    def test_three_products_render_without_empty_ranks(self):
        products = [
            {"label": "첫 번째 상품", "kg_price": 10000},
            {"label": "두 번째 상품", "kg_price": 20000},
            {"label": "매우 긴 상품명도 잘리지 않도록 확인하는 세 번째 상품", "kg_price": 30000},
        ]
        result = create_price_card_png("육회", products)
        with Image.open(BytesIO(result)) as image:
            self.assertEqual(image.size, (1080, 1350))

    def test_long_product_name_and_five_rows_render(self):
        products = [
            {
                "label": "[호주산] 냉동 홍두깨 채, 4mm (2kg×5ea) 아주 긴 상품 표시명",
                "kg_price": 20300 + index * 1000,
            }
            for index in range(5)
        ]
        result = create_price_card_png("육회", products)
        with Image.open(BytesIO(result)) as image:
            image.load()
            self.assertEqual(image.format, "PNG")
            self.assertEqual(image.size, (1080, 1350))
            self.assertGreater(len(result), 30_000)

    def test_generates_overall_and_category_market_reports(self):
        groups = [
            {
                "category_name": "한우",
                "items": [
                    {"item_name": "등심", "display_status": "연동 준비 중"},
                    {"item_name": "차돌박이", "kg_price": 23500},
                ],
            },
        ]
        overall = create_market_report_png("오늘의 축산물 실시간 단가", groups)
        category = create_market_report_png(
            "한우 실시간 단가", groups, canvas_size=CATEGORY_REPORT_SIZE,
        )
        with Image.open(BytesIO(overall)) as image:
            self.assertEqual(image.size, OVERALL_REPORT_SIZE)
        with Image.open(BytesIO(category)) as image:
            self.assertEqual(image.size, CATEGORY_REPORT_SIZE)

    @patch("price_card._load_product_image", return_value=None)
    def test_market_report_falls_back_to_text_when_product_image_fails(self, _load_image):
        groups = [{
            "category_name": "한우",
            "items": [{
                "item_name": "등심", "kg_price": 60100,
                "origin": "국내산", "storage_status": "냉장",
                "image_url": "https://static.ekcm.co.kr/broken.jpg",
                "image_status": "연결",
            }],
        }]
        result = create_market_report_png("한우 실시간 단가", groups)
        with Image.open(BytesIO(result)) as image:
            image.load()
            self.assertEqual(image.size, OVERALL_REPORT_SIZE)

    def test_official_logos_keep_their_original_aspect_ratio(self):
        from price_card import _load_official_logo

        dongwon = _load_official_logo("assets/logos/dongwon-group-official.png")
        geumcheon = _load_official_logo("assets/logos/geumcheon-meat-official.png")
        self.assertAlmostEqual(dongwon.width / dongwon.height, 889 / 501, places=2)
        self.assertAlmostEqual(geumcheon.width / geumcheon.height, 773 / 496, places=2)

    def test_qr_and_contact_phone_use_the_approved_values(self):
        from price_card import CONTACT_PHONE, _create_qr_image

        qr = _create_qr_image("https://open.kakao.com/o/sG85euyi", 126)
        self.assertEqual(CONTACT_PHONE, "010-6503-8953")
        self.assertEqual(qr.size, (126, 126))
        self.assertGreater(len(qr.getcolors(maxcolors=10)), 1)


if __name__ == "__main__":
    unittest.main()
