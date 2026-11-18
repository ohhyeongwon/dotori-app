"""Confirmed depletion is allowed; transport failures and ambiguous rows stay fatal."""
import ast
from copy import deepcopy
from datetime import datetime
from io import BytesIO
import logging
from pathlib import Path
import unittest
from unittest.mock import Mock, patch
from zoneinfo import ZoneInfo

from PIL import Image
import menu_data
import price_card


class SoldOutMarketTest(unittest.TestCase):
    def setUp(self):
        self.item = {
            'item_id': 'any_item', 'item_name': '냉장 테스트부위',
            'lookup': {'method': 'category', 'category_no': ('123', '456'),
                       'selection_policy': 'lowest_price_per_kg',
                       'exact_filters': {'ctmeatYn': 'N', 'strgMthdGbNm': '냉장'},
                       'filter_variants': [{'plspartNm': '테스트부위'}]},
        }
        self.row = dict(goodsNo=None, artcCd='article', goodsNm='브랜드_냉장테스트부위',
                        dispCtgNo='123', stkQty=0, salePrc=0,
                        saleEndDtm='2026-01-01 10:00:00')

    def confirm(self, row=None, status='ok', diagnostics=None):
        rows = [self.row if row is None else row]
        with patch('market_api.fetch_category_products', return_value={'status': status, 'items': rows}):
            return menu_data._confirm_market_item_sold_out(
                self.item, [{'status': 'ok'}] if diagnostics is None else diagnostics)

    def test_identified_ended_placeholder_is_sold_out_without_item_id_rule(self):
        self.assertEqual(self.confirm()['status'], 'sold_out')
        self.item['item_id'] = 'another_item'
        self.assertEqual(self.confirm()['status'], 'sold_out')

    def test_ambiguous_or_invalid_rows_are_not_sold_out(self):
        variants = [dict(dispCtgNo='other'), dict(goodsNm='무관한 상품'), dict(artcCd=None),
                    dict(stkQty=None), dict(stkQty=1), dict(stkQty='NaN'),
                    dict(salePrc=100), dict(salePrc='NaN'), dict(salePrc=-1),
                    dict(saleEndDtm=None), dict(saleEndDtm='bad-date'),
                    dict(saleEndDtm='2999-01-01'), dict(strgMthdGbNm='냉동'),
                    dict(ctmeatYn='Y'), dict(saleStatCd='unknown')]
        for changes in variants:
            with self.subTest(changes=changes):
                self.assertNotEqual(self.confirm({**self.row, **changes})['status'], 'sold_out')

    def test_api_errors_and_empty_responses_are_not_sold_out(self):
        self.assertEqual(self.confirm(status='error')['status'], 'error')
        self.assertNotEqual(self.confirm(diagnostics=[{'status': 'error'}])['status'], 'sold_out')
        with patch('market_api.fetch_category_products', return_value={'status': 'ok', 'items': []}):
            self.assertNotEqual(menu_data._confirm_market_item_sold_out(self.item, [{'status': 'ok'}])['status'], 'sold_out')

    def test_fixed_product_needs_matching_identity_and_explicit_end_state(self):
        self.item['lookup'] = {'method': 'goods', 'goods_no': '777', 'exact_filters': {'plspartNm': '테스트부위'}}
        row = dict(goodsNo='777', plspartNm='테스트부위', stkQty=0, salePrc=100,
                   saleStatCd='20', dispYn='N')
        with patch('market_api.fetch_goods_products', return_value={'status': 'ok', 'items': [row]}):
            self.assertEqual(menu_data._confirm_market_item_sold_out(self.item, [{'status': 'ok'}])['status'], 'sold_out')
            row['goodsNo'] = 'other'
            self.assertNotEqual(menu_data._confirm_market_item_sold_out(self.item, [{'status': 'ok'}])['status'], 'sold_out')

    def test_report_only_marks_confirmed_depletion(self):
        group = {'category_id': 'test', 'category_name': '테스트', 'items': [self.item]}
        for status, rows, expected in (
                ('ok', [self.row], 'sold_out'), ('error', [], None),
                ('ok', [{**self.row, 'saleEndDtm': None}], None)):
            with self.subTest(status=status, expected=expected), \
                 patch.object(menu_data, 'TODAY_MARKET_CATEGORIES', [group]), \
                 patch('market_api.get_market_prices', return_value={
                     'products': [], 'diagnostics': [{'status': status}],
                     'queried_at': datetime.now(ZoneInfo('Asia/Seoul'))}), \
                 patch('market_api.fetch_category_products', return_value={'status': status, 'items': rows}):
                report = menu_data.get_today_market_report(include_live_prices=True)
                item = report['groups'][0]['items'][0]
                self.assertEqual(item.get('availability_status'), expected)
                self.assertIsNone(item.get('kg_price'))
                self.assertEqual(item['display_status'], '품절' if expected else '현재 조회 불가')

    def test_network_failure_is_preserved_by_api_client(self):
        import requests
        import market_api
        market_api.fetch_category_products.clear()
        with patch('market_api.requests.post', side_effect=requests.ConnectionError('test network error')):
            response = market_api.fetch_category_products('network-failure-test')
        self.assertEqual(response['status'], 'error')
        market_api.fetch_category_products.clear()

    def refresh_scope(self, report):
        tree = ast.parse(Path('landing.py').read_text(encoding='utf-8'))
        fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == '_refresh_market_report_with_logs')
        scope = dict(CTA_UPGRADE_AVAILABLE=True, MARKET_REFRESH_LOGGER=logging.getLogger('sold-out-test'),
                     get_today_market_report=lambda *a, **kw: deepcopy(report),
                     create_market_report_png=Mock(), save_market_report=Mock(),
                     datetime=datetime, ZoneInfo=ZoneInfo, BytesIO=BytesIO, Image=Image,
                     KAKAO_CHAT_URL='', OVERALL_REPORT_SIZE=price_card.OVERALL_REPORT_SIZE,
                     A4_CTA_VERSION=price_card.A4_CTA_VERSION, A4_RENDER_PATH=price_card.A4_RENDER_PATH)
        exec(compile(ast.Module(body=[fn], type_ignores=[]), 'landing.py', 'exec'), scope)
        return scope

    def full_report(self):
        groups = deepcopy(menu_data.TODAY_MARKET_CATEGORIES)
        for group in groups:
            for item in group['items']:
                item['kg_price'] = 10000
        return dict(groups=groups, diagnostics=[], queried_at=datetime.now(ZoneInfo('Asia/Seoul')))

    def test_missing_network_error_and_wrong_count_block_refresh(self):
        for case in ('missing', 'source_error', 'wrong_count'):
            report = self.full_report()
            if case == 'missing':
                report['groups'][0]['items'][0]['kg_price'] = None
            elif case == 'source_error':
                report['diagnostics'] = [{'status': 'error'}]
            else:
                report['groups'][0]['items'].pop()
            scope = self.refresh_scope(report)
            with self.subTest(case=case), self.assertRaises(ValueError):
                scope['_refresh_market_report_with_logs']('failure')
            scope['create_market_report_png'].assert_not_called()
            scope['save_market_report'].assert_not_called()

    def test_any_confirmed_sold_out_item_can_refresh(self):
        report = self.full_report()
        item = report['groups'][0]['items'][0]
        item.update(kg_price=None, availability_status='sold_out', display_status='품절')
        scope = self.refresh_scope(report)
        scope['create_market_report_png'] = price_card.create_market_report_png
        scope['_refresh_market_report_with_logs']('success')
        scope['save_market_report'].assert_called_once()
        png = scope['save_market_report'].call_args.args[0]
        with Image.open(BytesIO(png)) as im:
            self.assertEqual(im.size, (2480, 3508))
            self.assertEqual(im.info['signup_cta_version'], price_card.A4_CTA_VERSION)

    def test_price_text_requires_confirmed_status_and_supports_both_flags(self):
        from PIL import ImageDraw
        original_text = ImageDraw.ImageDraw.text
        for flags, expected in (({}, '-'), ({'display_status': '품절'}, '품절'),
                                ({'availability_status': 'sold_out'}, '품절')):
            text = []
            def capture(draw, xy, value, *args, **kwargs):
                text.append(value)
                return original_text(draw, xy, value, *args, **kwargs)
            with patch.object(ImageDraw.ImageDraw, 'text', capture):
                price_card.create_market_report_png('test', [{'category_name': '테스트', 'items': [
                    {'item_id': 'arbitrary', 'item_name': '테스트', 'kg_price': None, **flags}]}])
            self.assertIn(expected, text)
            if not flags:
                self.assertNotIn('품절', text)


if __name__ == '__main__':
    unittest.main()
