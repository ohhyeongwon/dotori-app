"""금천미트 육회용 상품의 실시간 kg당 가격 조회."""

import logging
from decimal import Decimal, InvalidOperation

import requests
import streamlit as st


LOGGER = logging.getLogger(__name__)
GEUMCHEON_CATEGORY_URL = "https://gw.ekcm.co.kr/api/goods/v1/goods/dispGoodsList"
GEUMCHEON_GOODS_URL = "https://gw.ekcm.co.kr/api/goods/v1/goods/goodsList"
REQUEST_TIMEOUT_SECONDS = 8


def _positive_decimal(value):
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None
    return number if number > 0 else None


def _is_saleable(item):
    """실제 응답에서 확인한 판매·진열·재고 필드로 판매 가능 여부를 판정한다."""
    stock = _positive_decimal(item.get("stkQty"))
    return (
        item.get("saleStatCd") == "10"
        and item.get("dispYn") == "Y"
        and stock is not None
    )


def _normalize_item(item, source, input_order):
    """총 판매가격과 실제 판매 중량으로 kg당 가격을 계산한다."""
    if not _is_saleable(item):
        return None, "판매 불가 또는 재고 없음"

    sale_price = _positive_decimal(item.get("salePrc"))
    weight_kg = _positive_decimal(item.get("useEnabWgt"))
    if sale_price is None:
        return None, "판매가격 없음"
    if weight_kg is None:
        return None, "판매 중량 없음"

    kg_price = sale_price / weight_kg
    return {
        "label": source["label"],
        "goods_name": item.get("goodsNm") or source["label"],
        "goods_no": str(item.get("goodsNo", "")),
        "sale_price": int(sale_price),
        "weight_kg": float(weight_kg),
        "kg_price": float(kg_price),
        "source_type": source["type"],
        "source_id": source.get("category_no") or source.get("goods_no"),
        "input_order": input_order,
    }, None


def _category_request_body(category_no):
    return {
        "dispCtgNoList": [category_no],
        "brandNoList": [], "lsprdGrdCdList": [], "homeCdList": [],
        "ppYmdList": [], "strgMthdGbCdList": [], "workMethTypCdList": [],
        "deliProcTypCdList": [], "recomBkindList": [], "qualityList": [],
        "insfatGrdList": [], "mffldList": [], "estNoList": [],
        "sortTpCd": "60", "pageNo": 1, "pageSize": 500,
        "aplyPsbMediaCd": "01", "curCtgNo": category_no,
        "noDispCtgRegYn": "N", "mbrNo": "",
    }


@st.cache_data(ttl=300, show_spinner=False)
def fetch_category_products(category_no):
    """카테고리의 현재 판매 재고를 한 번에 조회한다."""
    try:
        response = requests.post(
            GEUMCHEON_CATEGORY_URL,
            json=_category_request_body(category_no),
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json().get("payload")
        if not isinstance(payload, list):
            raise ValueError("상품 배열이 없습니다.")
        return {"status": "ok", "items": payload}
    except (requests.RequestException, ValueError, AttributeError) as error:
        LOGGER.warning("금천미트 카테고리 조회 실패 category_no=%s reason=%s", category_no, error)
        return {"status": "error", "items": []}


@st.cache_data(ttl=300, show_spinner=False)
def fetch_goods_products(goods_numbers):
    """고정 goodsNo 상품을 한 번에 조회한다."""
    params = [("goodsNoList", goods_no) for goods_no in goods_numbers]
    params.append(("aplyPsbMediaCd", "01"))
    try:
        response = requests.get(
            GEUMCHEON_GOODS_URL,
            params=params,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json().get("payload")
        if not isinstance(payload, list):
            raise ValueError("상품 배열이 없습니다.")
        return {"status": "ok", "items": payload}
    except (requests.RequestException, ValueError, AttributeError) as error:
        LOGGER.warning("금천미트 고정 상품 조회 실패 goods_no=%s reason=%s", goods_numbers, error)
        return {"status": "error", "items": []}


def _select_category_product(source, input_order):
    response = fetch_category_products(source["category_no"])
    diagnostics = {
        "source": source["category_no"], "status": response["status"],
        "total_count": len(response["items"]), "valid_count": 0, "excluded_count": 0,
    }
    candidates = []
    for response_order, item in enumerate(response["items"]):
        normalized, _ = _normalize_item(item, source, input_order)
        if normalized is None:
            diagnostics["excluded_count"] += 1
            continue
        normalized["response_order"] = response_order
        candidates.append(normalized)

    diagnostics["valid_count"] = len(candidates)
    if not candidates:
        LOGGER.warning("금천미트 카테고리 유효 상품 없음 category_no=%s", source["category_no"])
        return None, diagnostics
    candidates.sort(key=lambda item: (item["kg_price"], item["response_order"]))
    return candidates[0], diagnostics


def _select_fixed_product(source, input_order, items_by_goods_no):
    item = items_by_goods_no.get(source["goods_no"])
    diagnostics = {
        "source": source["goods_no"], "status": "ok" if item else "missing",
        "total_count": 1 if item else 0, "valid_count": 0, "excluded_count": 0,
    }
    if item is None:
        LOGGER.warning("금천미트 고정 상품 응답 없음 goods_no=%s", source["goods_no"])
        return None, diagnostics
    normalized, reason = _normalize_item(item, source, input_order)
    if normalized is None:
        diagnostics["excluded_count"] = 1
        LOGGER.warning("금천미트 고정 상품 제외 goods_no=%s reason=%s", source["goods_no"], reason)
        return None, diagnostics
    diagnostics["valid_count"] = 1
    return normalized, diagnostics


def get_yukhoe_market_prices(sources):
    """카테고리 최저가와 고정 상품을 합쳐 kg당 가격 오름차순으로 반환한다."""
    products = []
    diagnostics = []
    goods_sources = [source for source in sources if source["type"] == "goods"]
    fixed_response = fetch_goods_products(tuple(source["goods_no"] for source in goods_sources))
    fixed_items = {
        str(item.get("goodsNo")): item for item in fixed_response["items"]
    } if fixed_response["status"] == "ok" else {}

    for input_order, source in enumerate(sources):
        if source["type"] == "category":
            selected, source_diagnostics = _select_category_product(source, input_order)
        else:
            selected, source_diagnostics = _select_fixed_product(
                source, input_order, fixed_items,
            )
            if fixed_response["status"] != "ok":
                source_diagnostics["status"] = "error"
        diagnostics.append(source_diagnostics)
        if selected is not None:
            products.append(selected)

    products.sort(key=lambda item: (item["kg_price"], item["input_order"]))
    return {"products": products, "diagnostics": diagnostics}
