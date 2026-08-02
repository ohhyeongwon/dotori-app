import unittest
from unittest.mock import Mock, patch

import market_api


def item(goods_no, price=20000, weight=1, stock=1, sale_status="10", displayed="Y"):
    return {
        "goodsNo": goods_no,
        "goodsNm": f"상품 {goods_no}",
        "salePrc": price,
        "useEnabWgt": weight,
        "stkQty": stock,
        "saleStatCd": sale_status,
        "dispYn": displayed,
    }


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
            result = market_api.get_yukhoe_market_prices(sources)
        self.assertEqual([product["goods_no"] for product in result["products"]], ["good"])

    def test_category_fetch_is_cached(self):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {"payload": [item("cached")]}
        with patch.object(market_api.requests, "post", return_value=response) as post:
            first = market_api.fetch_category_products("cache-test")
            second = market_api.fetch_category_products("cache-test")
        self.assertEqual(first, second)
        self.assertEqual(post.call_count, 1)

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
