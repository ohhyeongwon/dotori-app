"""검색 결과 카드에 사용하는 메뉴별 표시 데이터.

새 메뉴는 MENU_CARD_DATA에 같은 형식으로 추가할 수 있습니다.
등록되지 않은 기존 메뉴는 DEFAULT_CARD_DATA를 사용해 계속 검색됩니다.
"""

DEFAULT_CARD_DATA = {
    "specification": "업소용 정형 규격 · 상담 후 확정",
    "origin": "국내산·수입산 선택 가능",
    "market_price": "준비중",
    "stock_status": "준비중",
}

MENU_CARD_DATA = {
    "육회": {"specification": "냉장 정육 · 지방 제거 · 육회용 세절", "origin": "국내산 한우"},
    "쌀국수": {"specification": "차돌양지 · 국물용 덩어리/고명용 슬라이스", "origin": "호주산·미국산"},
    "갈비탕": {"specification": "탕갈비 · 5~7cm 절단", "origin": "미국산·호주산"},
    "삼겹살": {"specification": "미박삼겹 · 냉장/냉동 · 두께 상담", "origin": "국내산·수입산"},
    "제육볶음": {"specification": "돼지 전지 · 2mm 슬라이스", "origin": "국내산·수입산"},
    "돈가스": {"specification": "돼지 등심 · 연육 · 두께 상담", "origin": "국내산·수입산"},
    "감자탕": {"specification": "돼지 목뼈 · 절단 규격 상담", "origin": "캐나다산·유럽산·국내산"},
    "닭볶음탕": {"specification": "육계 10호 · 토막 정형", "origin": "국내산"},
    "삼계탕": {"specification": "삼계 5~6호 · 통닭", "origin": "국내산"},
    "보쌈": {"specification": "통삼겹 · 수육용 정형", "origin": "유럽산·국내산"},
    "등갈비": {"specification": "로인립 · 근막 제거 옵션", "origin": "유럽산·미국산·국내산"},
}


# 카테고리는 현재 판매 재고 중 kg당 최저가 1건을, 상품은 고정 goodsNo를 조회합니다.
YUKHOE_PRICE_SOURCES = [
    {
        "type": "category", "category_no": "130108",
        "label": "금천한우거세우둔살", "selection_policy": "lowest_price_per_kg",
    },
    {
        "type": "category", "category_no": "130109",
        "label": "금천한우거세홍두깨", "selection_policy": "lowest_price_per_kg",
    },
    {
        "type": "category", "category_no": "130106",
        "label": "금천한우거세꾸리살", "selection_policy": "lowest_price_per_kg",
    },
    {
        "type": "category", "category_no": "130110",
        "label": "금천한우거세설도", "selection_policy": "lowest_price_per_kg",
    },
    {
        "type": "goods", "goods_no": "27091248",
        "label": "[호주산] 냉동 홍두깨 채 4mm",
    },
]

# 이전 이름을 참조하는 코드와의 호환성을 유지합니다.
YUKHOE_PRODUCTS = YUKHOE_PRICE_SOURCES


STANDARD_MENU_DATA = {
    "육회": {
        "menu_name": "육회",
        "primary_cut": "우둔살",
        "alternative_cuts": ["꾸리살", "홍두깨살", "설도/설깃"],
        "specification": "냉장 정육 · 지방 제거 · 육회용 세절",
        "origin": "국내산 한우",
        "reason": "우둔살은 근육의 결이 일정하고 마블링(지방)이 적어 담백하며, 육회 고유의 진한 육향과 부드러운 탄력을 직관적으로 전달하는 표준 부위입니다.",
        "usage_tip": "생으로 먹는 육회는 마블링이 많으면 느끼합니다. 1등급 전후가 가장 찰지고 맛이 좋으며 등급보다는 도축 일자의 신선도가 핵심입니다.",
        "market_search_keyword": "",
        "product_codes": ["27091248"],
        "review_status": "검수 필요",
        "review_note": "생식용 원육 기준, 등급, 신선도, 냉장 및 세절 규격의 현장 검수가 필요합니다.",
        "field_reviews": {
            "primary_cut": "검수 필요", "alternative_cuts": "검수 필요",
            "specification": "검수 필요", "origin": "검수 필요",
            "reason": "검수 필요", "usage_tip": "검수 필요",
            "market_search_keyword": "미입력", "product_codes": "미입력",
        },
    },
    "삼겹살": {
        "menu_name": "삼겹살",
        "primary_cut": "미박삼겹(오겹살)",
        "alternative_cuts": ["일반삼겹", "대패삼겹"],
        "specification": "미박삼겹 · 냉장/냉동 · 두께 상담",
        "origin": "국내산·수입산",
        "reason": "껍데기가 붙어 있어 구웠을 때 껍데기의 쫀득함, 지방의 고소함, 살코기의 육즙 3박자가 극대화됩니다.",
        "usage_tip": "구이용 원육은 살코기와 지방층이 4:6 비율로 교차된 것이 가장 맛있습니다. 냉동 삼겹살은 3~4mm 두께가 육즙 손실을 막는 황금 두께입니다.",
        "market_search_keyword": "",
        "product_codes": [],
        "review_status": "검수 필요",
        "review_note": "냉장·냉동 선택 기준, 지방 비율과 3~4mm 두께의 현장 검수가 필요합니다.",
        "field_reviews": {
            "primary_cut": "검수 필요", "alternative_cuts": "검수 필요",
            "specification": "검수 필요", "origin": "검수 필요",
            "reason": "검수 필요", "usage_tip": "검수 필요",
            "market_search_keyword": "미입력", "product_codes": "미입력",
        },
    },
    "제육볶음": {
        "menu_name": "제육볶음",
        "primary_cut": "앞다리살(전지)",
        "alternative_cuts": ["뒷다리살(후지)", "대패삼겹살"],
        "specification": "돼지 전지 · 2mm 슬라이스",
        "origin": "국내산·수입산",
        "reason": "근육 사이에 적당한 지방층이 분포되어 있어 고온의 불길에 볶아내도 질겨지거나 퍽퍽해지지 않고 부드럽습니다.",
        "usage_tip": "볶음용 전지는 2mm 두께 슬라이스가 양념이 안쪽까지 가장 잘 배어드는 규격입니다.",
        "market_search_keyword": "",
        "product_codes": [],
        "review_status": "검수 필요",
        "review_note": "2mm 두께와 대체 원육별 사용 조건의 현장 검수가 필요합니다.",
        "field_reviews": {
            "primary_cut": "검수 필요", "alternative_cuts": "검수 필요",
            "specification": "검수 필요", "origin": "검수 필요",
            "reason": "검수 필요", "usage_tip": "검수 필요",
            "market_search_keyword": "미입력", "product_codes": "미입력",
        },
    },
    "돈가스": {
        "menu_name": "돈가스",
        "primary_cut": "등심",
        "alternative_cuts": ["안심", "후지(뒷다리)"],
        "specification": "돼지 등심 · 연육 · 두께 상담",
        "origin": "국내산·수입산",
        "reason": "적당한 육질의 단단함이 있어 튀김옷과의 밀착력이 우수하며, 튀겼을 때 씹는 맛이 직관적이고 고소합니다.",
        "usage_tip": "두툼한 일식 카츠의 경우, 미세 정교한 연육기(핀팅) 작업을 거치지 않으면 수축 현상이 일어나 튀김옷이 분리되므로 사전 연육육을 공급받는 게 마진에 이롭습니다.",
        "market_search_keyword": "",
        "product_codes": [],
        "review_status": "검수 필요",
        "review_note": "업장 유형별 두께와 연육 방식, 대체 원육의 적용 범위 검수가 필요합니다.",
        "field_reviews": {
            "primary_cut": "검수 필요", "alternative_cuts": "검수 필요",
            "specification": "검수 필요", "origin": "검수 필요",
            "reason": "검수 필요", "usage_tip": "검수 필요",
            "market_search_keyword": "미입력", "product_codes": "미입력",
        },
    },
    "갈비탕": {
        "menu_name": "갈비탕",
        "primary_cut": "본갈비(탕갈비)",
        "alternative_cuts": ["마구리", "찜갈비"],
        "specification": "탕갈비 · 5~7cm 절단",
        "origin": "미국산·호주산",
        "reason": "살밥이 두텁게 붙어 있어 그릇에 담아냈을 때 압도적인 비주얼을 자랑하며 씹었을 때 육즙이 가득합니다.",
        "usage_tip": "탕갈비와 마구리를 7:3 비율로 혼합 사용하는 것이 국물 퀄리티와 푸짐한 비주얼을 동시에 챙기는 외식업계 공식입니다.",
        "market_search_keyword": "",
        "product_codes": [],
        "review_status": "검수 필요",
        "review_note": "본갈비·탕갈비 명칭, 5~7cm 절단 규격과 7:3 혼합 비율의 현장 검수가 필요합니다.",
        "field_reviews": {
            "primary_cut": "검수 필요", "alternative_cuts": "검수 필요",
            "specification": "검수 필요", "origin": "검수 필요",
            "reason": "검수 필요", "usage_tip": "검수 필요",
            "market_search_keyword": "미입력", "product_codes": "미입력",
        },
    },
}


LEGACY_TO_STANDARD_FIELD_MAP = {
    "pro_pick": "primary_cut",
    "other_parts": "alternative_cuts",
    "pro_reason": "reason",
    "pro_tip": "usage_tip",
}


def get_card_data(menu_name):
    """메뉴별 카드 데이터를 기본값과 합쳐 반환한다."""
    return {**DEFAULT_CARD_DATA, **MENU_CARD_DATA.get(menu_name, {})}


def get_standard_menu_data(menu_name):
    """표준화한 대표 메뉴 데이터를 반환한다. 기존 UI에서는 아직 사용하지 않는다."""
    return STANDARD_MENU_DATA.get(menu_name)


def get_geumcheon_market_data(menu_name):
    """금천미트 가격/재고 데이터를 UI 형식으로 전달하는 연결 지점."""
    if menu_name != "육회":
        return {"market_price": "준비중", "stock_status": "준비중", "products": []}

    from market_api import get_yukhoe_market_prices

    result = get_yukhoe_market_prices(YUKHOE_PRICE_SOURCES)
    if not result["products"]:
        return {
            "market_price": "현재 실시간 가격을 불러올 수 없습니다.",
            "stock_status": "확인 예정",
            "products": [],
            "diagnostics": result["diagnostics"],
        }

    return {
        "market_price": "실시간 조회",
        "stock_status": f"판매 가능 {len(result['products'])}개",
        "products": result["products"],
        "diagnostics": result["diagnostics"],
    }
