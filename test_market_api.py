import unittest
from unittest.mock import Mock, patch

import market_api


def item(
    goods_no, price=20000, weight=1, stock=1, sale_status="10", displayed="Y",
    grade="1", brand="금천한우", goods_name=None, **fields,
):
    result = {
        "goodsNo": goods_no,
        "goodsNm": goods_name or f"상품 {goods_no}",
        "salePrc": price,
        "useEnabWgt": weight,
        "stkQty": stock,
        "saleStatCd": sale_status,
        "dispYn": displayed,
        "lsprdGrdNm": grade,
        "brandNm": brand,
        "goodsImgUrl": fields.pop("goodsImgUrl", ""),
    }
    result.update(fields)
    return result


class MarketApiTest(unittest.TestCase):
    def tearDown(self):
        market_api.fetch_category_products.clear()
        market_api.fetch_goods_products.clear()

    def test_invalid_products_are_excluded(self):
        source = {"type": "category", "category_no": "1", "label": "테스트"}
        response = {
            "status": "ok",
            "items": [
                item("sold-out", stock=0),
                item("no-price", price=0),
                item("no-weight", weight=0),
                item("stopped", sale_status="20"),
                item("hidden", displayed="N"),
                item("valid", price=15000, weight=1),
            ],
        }
        with patch.object(market_api, "fetch_category_products", return_value=response):
            selected, diagnostics = market_api._select_category_product(source, 0)
        self.assertEqual(selected["goods_no"], "valid")
        self.assertEqual(diagnostics["valid_count"], 1)
        self.assertEqual(diagnostics["excluded_count"], 5)

    def test_excluded_goods_name_keywords_are_rejected(self):
        source = {
            "type": "category", "category_no": "1", "label": "백립",
            "exact_filters": {"homeNm": "미국"},
            "excluded_name_keywords": ["절단", "소포장"],
        }
        response = {
            "status": "ok",
            "items": [
                item("cut", goods_name="냉동우빽립 절단", homeNm="미국"),
                item("small", goods_name="냉동우빽립 소포장", homeNm="미국"),
                item("raw", goods_name="냉동우빽립 벌크", homeNm="미국"),
            ],
        }
        with patch.object(market_api, "fetch_category_products", return_value=response):
            selected, diagnostics = market_api._select_category_product(source, 0)
        self.assertEqual(selected["goods_no"], "raw")
        self.assertEqual(diagnostics["filter_match_count"], 1)
        self.assertEqual(selected["applied_filters"]["goodsNm_excludes"], ["절단", "소포장"])
        self.assertEqual(diagnostics["excluded_count"], 2)

    def test_required_goods_name_keywords_limit_the_comparison_group(self):
        source = {
            "type": "category", "category_no": "1", "label": "전각",
            "required_name_keywords_all": ["전각", "불고기"],
            "excluded_name_keywords": ["다짐육"],
        }
        response = {
            "status": "ok",
            "items": [
                item("ground", goods_name="냉동전각 다짐육", price=5000),
                item("other", goods_name="냉동갈비 불고기", price=6000),
                item("valid", goods_name="냉동전각 불고기", price=7000),
            ],
        }
        with patch.object(market_api, "fetch_category_products", return_value=response):
            selected, diagnostics = market_api._select_category_product(source, 0)
        self.assertEqual(selected["goods_no"], "valid")
        self.assertEqual(diagnostics["filter_match_count"], 1)
        self.assertEqual(selected["applied_filters"]["goodsNm_includes_all"], ["전각", "불고기"])

    def test_lowest_price_and_equal_price_order_are_stable(self):
        source = {"type": "category", "category_no": "1", "label": "테스트"}
        response = {
            "status": "ok",
            "items": [
                item("first", price=20000, weight=2),
                item("same-price-later", price=10000, weight=1),
                item("expensive", price=15000, weight=1),
            ],
        }
        with patch.object(market_api, "fetch_category_products", return_value=response):
            selected, _ = market_api._select_category_product(source, 0)
        self.assertEqual(selected["goods_no"], "first")
        self.assertEqual(selected["kg_price"], 10000)
        self.assertEqual(selected["kg_price_rounded"], 10000)

    def test_exact_filters_do_not_include_plus_grades_or_other_brands(self):
        response = {
            "status": "ok",
            "items": [
                item("grade-plus", price=10000, grade="1+"),
                item("other-brand", price=11000, grade="1", brand="외부한우"),
                item("exact", price=12000, grade="1", brand="금천한우"),
            ],
        }
        source = {
            "type": "category", "category_no": "1", "label": "등심",
            "exact_filters": {"lsprdGrdNm": "1", "brandNm": "금천한우"},
        }
        with patch.object(market_api, "fetch_category_products", return_value=response):
            selected, diagnostics = market_api._select_category_product(source, 0)
        self.assertEqual(selected["goods_no"], "exact")
        self.assertEqual(diagnostics["filter_match_count"], 1)
        self.assertEqual(diagnostics["valid_count"], 1)

    def test_one_category_failure_does_not_remove_other_results(self):
        sources = [
            {"type": "category", "category_no": "bad", "label": "실패"},
            {"type": "category", "category_no": "good", "label": "정상"},
        ]

        def category_response(category_no):
            if category_no == "bad":
                return {"status": "error", "items": []}
            return {"status": "ok", "items": [item("good", 12000, 1)]}

        with (
            patch.object(market_api, "fetch_category_products", side_effect=category_response),
            patch.object(market_api, "fetch_goods_products", return_value={"status": "ok", "items": []}),
        ):
            result = market_api.get_market_prices(sources)
        self.assertEqual([product["goods_no"] for product in result["products"]], ["good"])

    def test_selected_product_preserves_its_official_image_metadata(self):
        source = {"type": "category", "category_no": "image", "label": "등심"}
        response = {
            "status": "ok",
            "items": [item(
                "with-image", 12000, 1,
                goodsImgUrl="https://static.ekcm.co.kr/files/goods/example.jpg",
            )],
        }
        with patch.object(market_api, "fetch_category_products", return_value=response):
            result = market_api.get_market_prices([source])
        product = result["products"][0]
        self.assertEqual(product["image_status"], "연결")
        self.assertEqual(product["image_source"], "금천미트 API goodsImgUrl")
        self.assertEqual(product["image_url"], response["items"][0]["goodsImgUrl"])

    def test_keyword_source_is_ready_without_api_guessing(self):
        result = market_api.get_market_prices([
            {"type": "keyword", "search_keyword": "한우 등심", "label": "한우 등심"},
        ])
        self.assertEqual(result["products"], [])
        self.assertEqual(result["diagnostics"][0]["status"], "not_connected")

    def test_category_fetch_is_cached(self):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {"payload": [item("cached")]}
        with patch.object(market_api.requests, "post", return_value=response) as post:
            first = market_api.fetch_category_products("cache-test")
            second = market_api.fetch_category_products("cache-test")
        self.assertEqual(first, second)
        self.assertEqual(post.call_count, 1)

    def test_category_fetch_reads_all_pages_and_deduplicates_goods_numbers(self):
        first_page = [item(str(index)) for index in range(500)]
        second_page = [item("499"), item("500")]
        for product in first_page + second_page:
            product["totCnt"] = 501
        responses = []
        for payload in (first_page, second_page):
            response = Mock()
            response.raise_for_status.return_value = None
            response.json.return_value = {"payload": payload}
            responses.append(response)
        with patch.object(market_api.requests, "post", side_effect=responses) as post:
            result = market_api.fetch_category_products(("a", "b"))
        self.assertEqual(result["status"], "ok")
        self.assertEqual(len(result["items"]), 501)
        self.assertEqual(result["page_count"], 2)
        self.assertEqual(post.call_count, 2)
        self.assertEqual(post.call_args_list[1].kwargs["json"]["pageNo"], 2)
        self.assertEqual(post.call_args_list[0].kwargs["json"]["dispCtgNoList"], ["a", "b"])

    def test_timeout_returns_error_instead_of_raising(self):
        with patch.object(
            market_api.requests,
            "post",
            side_effect=market_api.requests.Timeout("timeout"),
        ):
            result = market_api.fetch_category_products("timeout-test")
        self.assertEqual(result, {"status": "error", "items": []})


if __name__ == "__main__":
    unittest.main()
