"""금천미트 상품 소스를 공통 형식으로 조회해 kg당 가격을 계산한다."""

import logging
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
import streamlit as st


LOGGER = logging.getLogger(__name__)
GEUMCHEON_CATEGORY_URL = "https://gw.ekcm.co.kr/api/goods/v1/goods/dispGoodsList"
GEUMCHEON_GOODS_URL = "https://gw.ekcm.co.kr/api/goods/v1/goods/goodsList"
REQUEST_TIMEOUT_SECONDS = 8
KST = ZoneInfo("Asia/Seoul")


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


def _matches_source_filters(item, source):
    """승인된 API 원본 필드 필터를 문자열 정확 일치로만 적용한다."""
    exact_match = all(
        str(item.get(field, "")) == str(expected)
        for field, expected in source.get("exact_filters", {}).items()
    )
    goods_name = str(item.get("goodsNm") or "")
    excluded_keywords = source.get("excluded_name_keywords", [])
    required_any = source.get("required_name_keywords_any", [])
    required_all = source.get("required_name_keywords_all", [])
    return (
        exact_match
        and not any(keyword in goods_name for keyword in excluded_keywords)
        and (not required_any or any(keyword in goods_name for keyword in required_any))
        and all(keyword in goods_name for keyword in required_all)
    )


def _applied_filters(source):
    filters = dict(source.get("exact_filters", {}))
    excluded_keywords = source.get("excluded_name_keywords", [])
    if excluded_keywords:
        filters["goodsNm_excludes"] = list(excluded_keywords)
    required_any = source.get("required_name_keywords_any", [])
    required_all = source.get("required_name_keywords_all", [])
    if required_any:
        filters["goodsNm_includes_any"] = list(required_any)
    if required_all:
        filters["goodsNm_includes_all"] = list(required_all)
    return filters


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
    kg_price_rounded = int(kg_price.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    image_url = item.get("goodsImgUrl") or ""
    return {
        "label": source["label"],
        "goods_name": item.get("goodsNm") or source["label"],
        "goods_no": str(item.get("goodsNo", "")),
        "sale_price": int(sale_price),
        "weight_kg": float(weight_kg),
        "kg_price": float(kg_price),
        "kg_price_rounded": kg_price_rounded,
        "grade": item.get("lsprdGrdNm") or "",
        "livestock": item.get("lsspeNm") or "",
        "part": item.get("plspartNm") or "",
        "processing_status": "세절" if item.get("ctmeatYn") == "Y" else "비세절",
        "ctmeat_yn": item.get("ctmeatYn") or "",
        "brand": item.get("brandNm") or "",
        "origin": item.get("homeNm") or "",
        "storage_status": item.get("strgMthdGbNm") or "",
        "image_url": image_url,
        "image_source": "금천미트 API goodsImgUrl" if image_url else "",
        "image_status": "연결" if image_url else "미연결",
        "applied_filters": _applied_filters(source),
        "source_type": source["type"],
        "source_id": source.get("category_no") or source.get("goods_no"),
        "input_order": input_order,
    }, None


def _category_request_body(category_no):
    category_numbers = (
        list(category_no) if isinstance(category_no, (list, tuple)) else [category_no]
    )
    return {
        "dispCtgNoList": category_numbers,
        "brandNoList": [], "lsprdGrdCdList": [], "homeCdList": [],
        "ppYmdList": [], "strgMthdGbCdList": [], "workMethTypCdList": [],
        "deliProcTypCdList": [], "recomBkindList": [], "qualityList": [],
        "insfatGrdList": [], "mffldList": [], "estNoList": [],
        "sortTpCd": "60", "pageNo": 1, "pageSize": 500,
        "aplyPsbMediaCd": "01", "curCtgNo": category_numbers[0],
        "noDispCtgRegYn": "N", "mbrNo": "",
    }


@st.cache_data(ttl=300, show_spinner=False)
def fetch_category_products(category_no):
    """카테고리의 모든 페이지를 조회하고 goodsNo 중복을 제거한다."""
    try:
        page_number = 1
        total_count = None
        unique_items = {}
        while total_count is None or len(unique_items) < total_count:
            request_body = _category_request_body(category_no)
            request_body["pageNo"] = page_number
            response = requests.post(
                GEUMCHEON_CATEGORY_URL,
                json=request_body,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            payload = response.json().get("payload")
            if not isinstance(payload, list):
                raise ValueError("상품 배열이 없습니다.")
            if not payload:
                break
            if total_count is None:
                total_count = int(payload[0].get("totCnt") or len(payload))
            previous_count = len(unique_items)
            for item in payload:
                unique_items.setdefault(str(item.get("goodsNo", "")), item)
            if len(payload) < request_body["pageSize"] or len(unique_items) == previous_count:
                break
            page_number += 1
        return {
            "status": "ok", "items": list(unique_items.values()),
            "page_count": page_number,
        }
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
        "total_count": len(response["items"]), "filter_match_count": 0,
        "valid_count": 0, "excluded_count": 0,
        "applied_filters": _applied_filters(source),
    }
    candidates = []
    for response_order, item in enumerate(response["items"]):
        if not _matches_source_filters(item, source):
            diagnostics["excluded_count"] += 1
            continue
        diagnostics["filter_match_count"] += 1
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


def get_market_prices(sources):
    """카테고리·고정 상품 소스를 합쳐 kg당 가격 오름차순으로 반환한다."""
    products = []
    diagnostics = []
    goods_sources = [source for source in sources if source["type"] == "goods"]
    fixed_response = (
        fetch_goods_products(tuple(source["goods_no"] for source in goods_sources))
        if goods_sources
        else {"status": "ok", "items": []}
    )
    fixed_items = {
        str(item.get("goodsNo")): item for item in fixed_response["items"]
    } if fixed_response["status"] == "ok" else {}

    for input_order, source in enumerate(sources):
        if source["type"] == "category":
            selected, source_diagnostics = _select_category_product(source, input_order)
        elif source["type"] == "goods":
            selected, source_diagnostics = _select_fixed_product(
                source, input_order, fixed_items,
            )
            if fixed_response["status"] != "ok":
                source_diagnostics["status"] = "error"
        else:
            selected = None
            source_diagnostics = {
                "source": source.get("search_keyword") or source.get("label", ""),
                "status": "not_connected",
                "total_count": 0,
                "valid_count": 0,
                "excluded_count": 0,
            }
            LOGGER.info("금천미트 검색어 조회는 아직 연결 전입니다. source=%s", source)
        diagnostics.append(source_diagnostics)
        if selected is not None:
            products.append(selected)

    products.sort(key=lambda item: (item["kg_price"], item["input_order"]))
    return {
        "products": products,
        "diagnostics": diagnostics,
        "queried_at": datetime.now(KST),
    }


def get_yukhoe_market_prices(sources):
    """기존 육회 호출부와 테스트를 위한 공통 조회 함수 호환 별칭."""
    return get_market_prices(sources)
