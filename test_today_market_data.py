import unittest
from unittest.mock import patch

from menu_data import TODAY_MARKET_CATEGORIES, get_today_market_report


class TodayMarketDataTest(unittest.TestCase):
    def test_category_and_item_order(self):
        self.assertEqual(
            [category["category_name"] for category in TODAY_MARKET_CATEGORIES],
            ["한우", "육우", "한돈", "수입 소고기", "수입 돼지고기", "닭고기", "세절육"],
        )
        self.assertEqual(
            [item["item_name"] for item in TODAY_MARKET_CATEGORIES[0]["items"]],
            ["등심", "차돌박이", "우둔"],
        )

    def test_every_item_has_common_lookup_shape(self):
        required = {
            "method", "category_no", "goods_no", "search_keyword", "selection_policy",
        }
        items = [item for category in TODAY_MARKET_CATEGORIES for item in category["items"]]
        self.assertEqual(len(items), 17)
        for item in items:
            self.assertTrue(required.issubset(item["lookup"]))
            self.assertIn(item["lookup"]["method"], {None, "category", "goods", "keyword"})
            self.assertEqual(item["display_status"], "연동 준비 중")
            self.assertEqual(item["image_url"], "")
            self.assertEqual(item["image_source"], "")
            self.assertEqual(item["image_status"], "미연결")

    def test_only_explicit_origin_and_storage_are_prefilled(self):
        items = {
            item["item_id"]: item
            for category in TODAY_MARKET_CATEGORIES
            for item in category["items"]
        }
        self.assertEqual(items["handon_belly"]["storage_status"], "냉장")
        self.assertEqual(items["brazil_frozen_chicken_thigh"]["origin"], "브라질산")
        self.assertEqual(items["brazil_frozen_chicken_thigh"]["storage_status"], "냉동")
        self.assertEqual(items["hanwoo_sirloin"]["origin"], "")
        self.assertEqual(items["hanwoo_round"]["lookup"]["category_no"], "130108")

    def test_only_three_approved_import_items_are_connected(self):
        items = {
            item["item_id"]: item
            for category in TODAY_MARKET_CATEGORIES
            for item in category["items"]
        }
        self.assertEqual(items["imported_beef_back_rib"]["lookup"]["category_no"], "420109")
        self.assertEqual(items["imported_beef_shank"]["lookup"]["category_no"], "420120")
        self.assertEqual(items["brazil_frozen_chicken_thigh"]["lookup"]["category_no"], "814909")
        self.assertEqual(items["imported_beef_intercostal"]["lookup"]["category_no"], "410103")
        self.assertEqual(len(items["imported_pork_frozen_belly"]["lookup"]["category_no"]), 8)
        self.assertEqual(len(items["imported_pork_neck_picnic"]["lookup"]["category_no"]), 3)
        self.assertIn("API상 원물 공식 필드 확인 불가", items["imported_beef_back_rib"]["review_note"])

    def test_yukwoo_and_handon_connections_follow_reviewed_categories(self):
        items = {
            item["item_id"]: item
            for category in TODAY_MARKET_CATEGORIES
            for item in category["items"]
        }
        self.assertEqual(items["beef_cattle_striploin"]["lookup"]["exact_filters"]["lsprdGrdNm"], "2")
        self.assertEqual(items["beef_cattle_knuckle"]["lookup"]["exact_filters"]["plspartNm"], "설깃")
        self.assertEqual(items["handon_belly"]["lookup"]["exact_filters"]["skngStatNm"], "박피")
        self.assertEqual(items["handon_neck"]["lookup"]["exact_filters"]["plspartNm"], "목심")
        self.assertEqual(items["handon_picnic"]["lookup"]["exact_filters"]["plspartNm"], "앞다리")
        self.assertEqual(items["sliced_beef_belly"]["lookup"]["category_no"], "813348")
        self.assertEqual(items["sliced_pork_neck_picnic"]["lookup"]["category_no"], "813367")
        self.assertEqual(items["sliced_beef_bulgogi"]["lookup"]["category_no"], "813352")

    def test_report_selection_returns_only_requested_category(self):
        overall = get_today_market_report()
        hanwoo = get_today_market_report("hanwoo")
        self.assertEqual(len(overall["groups"]), 7)
        self.assertEqual(hanwoo["title"], "한우 실시간 단가")
        self.assertEqual([group["category_name"] for group in hanwoo["groups"]], ["한우"])

    def test_live_prices_and_selection_details_are_merged_into_hanwoo_items(self):
        from datetime import datetime

        queried_at = datetime(2026, 8, 3, 13, 30)
        response = {
            "products": [
                {
                    "source_type": "category", "source_id": category_no,
                    "kg_price": kg_price, "goods_no": f"verified-{category_no}",
                    "goods_name": "검증 상품", "grade": grade,
                    "brand": "금천한우", "sale_price": kg_price * 10,
                    "weight_kg": 10.0, "applied_filters": filters,
                    "image_url": f"https://static.ekcm.co.kr/{category_no}.jpg",
                    "image_source": "금천미트 API goodsImgUrl", "image_status": "연결",
                }
                for category_no, kg_price, grade, filters in [
                    ("130102", 60100, "1", {"lsprdGrdNm": "1"}),
                    ("130128", 42900, "3", {"brandNm": "금천한우"}),
                    ("130108", 29900, "2", {}),
                ]
            ],
            "diagnostics": [],
            "queried_at": queried_at,
        }
        with patch("market_api.get_market_prices", return_value=response):
            report = get_today_market_report("hanwoo", include_live_prices=True)
        items = {item["item_id"]: item for item in report["groups"][0]["items"]}
        self.assertEqual(items["hanwoo_sirloin"]["kg_price"], 60100)
        self.assertEqual(items["hanwoo_brisket"]["kg_price"], 42900)
        self.assertEqual(items["hanwoo_round"]["kg_price"], 29900)
        self.assertEqual(items["hanwoo_sirloin"]["grade"], "1")
        self.assertEqual(items["hanwoo_brisket"]["review_note"], "원물·세절 여부 현장 확인 필요")
        self.assertEqual(items["hanwoo_round"]["queried_at"], queried_at)
        self.assertEqual(items["hanwoo_sirloin"]["image_status"], "연결")
        self.assertEqual(items["hanwoo_sirloin"]["image_source"], "금천미트 API goodsImgUrl")


if __name__ == "__main__":
    unittest.main()
