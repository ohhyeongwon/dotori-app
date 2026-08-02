import unittest
from datetime import datetime
from io import BytesIO
from zoneinfo import ZoneInfo

from PIL import Image

from price_card import create_price_card_png


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


if __name__ == "__main__":
    unittest.main()
