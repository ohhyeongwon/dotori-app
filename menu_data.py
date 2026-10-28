"""검색 결과 카드에 사용하는 메뉴별 표시 데이터.

새 메뉴는 MENU_CARD_DATA에 같은 형식으로 추가할 수 있습니다.
등록되지 않은 기존 메뉴는 DEFAULT_CARD_DATA를 사용해 계속 검색됩니다.
"""

from copy import deepcopy

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


# 메인 고정 단가표의 표시 순서와 향후 조회 연결 정보를 함께 관리합니다.
# lookup.method는 category, goods, keyword 중 하나를 선택하며, 연결 전에는 None입니다.
TODAY_MARKET_CATEGORIES = [
    {
        "category_id": "hanwoo", "category_name": "한우", "report_color": "#6F4435",
        "items": [
            {"item_id": "hanwoo_sirloin", "item_name": "등심"},
            {"item_id": "hanwoo_brisket", "item_name": "차돌박이"},
            {"item_id": "hanwoo_round", "item_name": "우둔"},
        ],
    },
    {
        "category_id": "beef_cattle", "category_name": "육우", "report_color": "#8A6239",
        "items": [
            {"item_id": "beef_cattle_striploin", "item_name": "채끝"},
            {"item_id": "beef_cattle_knuckle", "item_name": "설깃"},
        ],
    },
    {
        "category_id": "handon", "category_name": "한돈", "report_color": "#A75D50",
        "items": [
            {"item_id": "handon_belly", "item_name": "냉장 삼겹살"},
            {"item_id": "handon_neck", "item_name": "냉장 목살"},
            {"item_id": "handon_picnic", "item_name": "냉장 앞다리살"},
        ],
    },
    {
        "category_id": "imported_beef", "category_name": "수입 소고기", "report_color": "#243B63",
        "items": [
            {"item_id": "imported_beef_intercostal", "item_name": "늑간"},
            {"item_id": "imported_beef_back_rib", "item_name": "백립"},
            {"item_id": "imported_beef_shank", "item_name": "아롱사태"},
        ],
    },
    {
        "category_id": "imported_pork", "category_name": "수입 돼지고기", "report_color": "#1F6A68",
        "items": [
            {"item_id": "imported_pork_frozen_belly", "item_name": "냉동 삼겹살"},
            {"item_id": "imported_pork_neck_picnic", "item_name": "목전지"},
        ],
    },
    {
        "category_id": "chicken", "category_name": "닭고기", "report_color": "#6F793D",
        "items": [
            {"item_id": "brazil_frozen_chicken_thigh", "item_name": "브라질산 냉동 닭정육"},
        ],
    },
    {
        "category_id": "sliced_meat", "category_name": "세절육", "report_color": "#6E2838",
        "items": [
            {"item_id": "sliced_beef_belly", "item_name": "우삼겹"},
            {"item_id": "sliced_pork_neck_picnic", "item_name": "목전지"},
            {"item_id": "sliced_beef_bulgogi", "item_name": "소불고기(전각)"},
        ],
    },
]

for market_category in TODAY_MARKET_CATEGORIES:
    for market_item in market_category["items"]:
        market_item["lookup"] = {
            "method": None,
            "category_no": "",
            "goods_no": "",
            "search_keyword": "",
            "selection_policy": "lowest_price_per_kg",
        }
        market_item["display_status"] = "연동 준비 중"
        market_item["origin"] = ""
        market_item["storage_status"] = ""
        market_item["image_url"] = ""
        market_item["image_source"] = ""
        market_item["image_status"] = "미연결"

# 품목명에서 이미 명시된 사실만 구조에 반영합니다.
for market_category in TODAY_MARKET_CATEGORIES:
    for market_item in market_category["items"]:
        if market_item["item_name"].startswith("냉장 "):
            market_item["storage_status"] = "냉장"
        elif "냉동" in market_item["item_name"]:
            market_item["storage_status"] = "냉동"
        if market_item["item_id"] == "brazil_frozen_chicken_thigh":
            market_item["origin"] = "브라질산"

# 승인된 한우 단가 기준입니다. 필터는 API 원본 필드의 정확 일치만 사용합니다.
for market_category in TODAY_MARKET_CATEGORIES:
    for market_item in market_category["items"]:
        if market_item["item_id"] == "hanwoo_sirloin":
            market_item["lookup"].update({
                "method": "category", "category_no": "130102",
                "exact_filters": {"lsprdGrdNm": "1"},
            })
            market_item["review_note"] = "1등급 상품만 비교"
        elif market_item["item_id"] == "hanwoo_brisket":
            market_item["lookup"].update({
                "method": "category", "category_no": "130128",
                "exact_filters": {"brandNm": "금천한우"},
            })
            market_item["review_note"] = "원물·세절 여부 현장 확인 필요"
        elif market_item["item_id"] == "hanwoo_round":
            market_item["lookup"].update({
                "method": "category", "category_no": "130108",
                "exact_filters": {},
            })
            market_item["review_note"] = "현재 판매 가능한 전체 후보 비교"

# 승인된 수입 냉동육 3개 품목만 실시간 단가에 연결합니다.
RAW_CANDIDATE_REVIEW_NOTE = (
    "API상 원물 공식 필드 확인 불가. 카테고리·상품명·ctmeatYn 기준으로 원물 후보 처리"
)
RAW_CANDIDATE_EXCLUDED_KEYWORDS = [
    "양념", "절단", "세절", "슬라이스", "큐브", "소포장",
]
for market_category in TODAY_MARKET_CATEGORIES:
    for market_item in market_category["items"]:
        if market_item["item_id"] == "imported_beef_back_rib":
            market_item["lookup"].update({
                "method": "category", "category_no": "420109",
                "exact_filters": {
                    "homeNm": "미국", "strgMthdGbNm": "냉동",
                    "plspartNm": "우빽립", "lsspeNm": "수입우", "ctmeatYn": "N",
                },
                "excluded_name_keywords": RAW_CANDIDATE_EXCLUDED_KEYWORDS,
            })
            market_item["review_note"] = RAW_CANDIDATE_REVIEW_NOTE
        elif market_item["item_id"] == "imported_beef_shank":
            market_item["lookup"].update({
                "method": "category", "category_no": "420120",
                "exact_filters": {
                    "homeNm": "미국", "strgMthdGbNm": "냉동",
                    "plspartNm": "아롱사태", "lsspeNm": "수입우", "ctmeatYn": "N",
                },
                "excluded_name_keywords": RAW_CANDIDATE_EXCLUDED_KEYWORDS,
            })
            market_item["review_note"] = RAW_CANDIDATE_REVIEW_NOTE
        elif market_item["item_id"] == "brazil_frozen_chicken_thigh":
            market_item["lookup"].update({
                "method": "category", "category_no": "814909",
                "exact_filters": {
                    "homeNm": "브라질", "strgMthdGbNm": "냉동",
                    "plspartNm": "닭정육", "lsspeNm": "수입닭",
                },
            })
            market_item["review_note"] = "브라질산 냉동 닭정육 전체 규격 비교"

# 링크에서 확인된 수입 원육 전용 카테고리입니다. API에 원물 공식 필드가 없어
# 수입 축종·부위·보관 상태·ctmeatYn과 가공 키워드 제외 기준을 함께 적용합니다.
IMPORT_RAW_REVIEW_NOTE = (
    "API상 원판·원물 공식 필드 확인 불가. 전용 카테고리·상품명·ctmeatYn 기준으로 후보 처리"
)
for market_category in TODAY_MARKET_CATEGORIES:
    for market_item in market_category["items"]:
        if market_item["item_id"] == "imported_beef_intercostal":
            market_item["lookup"].update({
                "method": "category", "category_no": "410103",
                "exact_filters": {
                    "strgMthdGbNm": "냉장", "plspartNm": "늑간살",
                    "lsspeNm": "수입우", "ctmeatYn": "N",
                },
                "excluded_name_keywords": [
                    "양념", "절단", "세절", "슬라이스", "큐브", "소포장",
                ],
            })
            market_item["review_note"] = IMPORT_RAW_REVIEW_NOTE
        elif market_item["item_id"] == "imported_pork_frozen_belly":
            market_item["lookup"].update({
                "method": "category",
                "category_no": (
                    "520111", "520324", "520414", "812879",
                    "812889", "812904", "812917", "812925",
                ),
                "exact_filters": {
                    "strgMthdGbNm": "냉동", "plspartNm": "삼겹",
                    "lsspeNm": "수입돈", "ctmeatYn": "N",
                },
                "excluded_name_keywords": [
                    "슬라이스", "대패", "세절", "큐브", "구이용", "절단",
                    "소포장", "양념", "3P", "4P", "개별",
                ],
            })
            market_item["review_note"] = (
                f"{IMPORT_RAW_REVIEW_NOTE}. 3P·4P·개별 표기는 성격 확정 불가로 제외"
            )
        elif market_item["item_id"] == "imported_pork_neck_picnic":
            market_item["lookup"].update({
                "method": "category",
                "category_no": ("520109", "520313", "812754"),
                "exact_filters": {
                    "strgMthdGbNm": "냉동", "plspartNm": "목전지",
                    "lsspeNm": "수입돈", "ctmeatYn": "N",
                },
                "excluded_name_keywords": [
                    "슬라이스", "제육", "세절", "큐브", "절단", "소포장",
                    "양념", "2P", "개별",
                ],
            })
            market_item["review_note"] = (
                f"{IMPORT_RAW_REVIEW_NOTE}. 2P 표기는 성격 확정 불가로 제외"
            )

# 육우 채끝은 등급별 가격 차이가 커 승인 전까지 연결하지 않습니다.
# 나머지 4개 품목은 링크 카테고리 전체의 부위·보관·규격이 일관된 경우만 연결합니다.
for market_category in TODAY_MARKET_CATEGORIES:
    for market_item in market_category["items"]:
        if market_item["item_id"] == "beef_cattle_striploin":
            market_item["display_status"] = "현재 조회 불가"
            market_item["review_note"] = (
                "1++·1+·1·2·3등급 혼재 및 등급별 최저가 차이로 대표 등급 승인 필요"
            )
        elif market_item["item_id"] == "beef_cattle_knuckle":
            market_item["lookup"].update({
                "method": "category",
                "category_no": (
                    "210111", "210211", "210315", "210417", "210510", "210611",
                ),
                "exact_filters": {
                    "homeNm": "국내산", "strgMthdGbNm": "냉장",
                    "plspartNm": "설깃", "lsspeNm": "육우", "ctmeatYn": "N",
                },
            })
            market_item["review_note"] = "링크 카테고리 전체가 API상 설깃으로 구성"
        elif market_item["item_id"] == "handon_belly":
            market_item["lookup"].update({
                "method": "category",
                "category_no": (
                    "310103", "310201", "310301", "310401", "310701", "310801",
                    "311001", "810665", "811174", "812239", "812794", "815079",
                    "815277", "815954", "816754", "817594", "818255",
                ),
                "exact_filters": {
                    "homeNm": "국내산", "strgMthdGbNm": "냉장",
                    "plspartNm": "삼겹", "lsspeNm": "한돈", "ctmeatYn": "N",
                    "skngStatNm": "박피",
                },
                "excluded_name_keywords": [
                    "슬라이스", "대패", "세절", "큐브", "구이용", "절단",
                    "소포장", "양념", "냉동", "수입",
                ],
            })
            market_item["review_note"] = "링크 카테고리 전체 901건이 API상 박피 삼겹으로 구성"
        elif market_item["item_id"] == "handon_neck":
            market_item["lookup"].update({
                "method": "category",
                "category_no": (
                    "310108", "310203", "310303", "310403", "310703", "310803",
                    "311003", "311102", "810676", "811194", "812237", "812792",
                    "815077", "815274", "815974", "816755", "817604", "818256",
                ),
                "exact_filters": {
                    "homeNm": "국내산", "strgMthdGbNm": "냉장",
                    "plspartNm": "목심", "lsspeNm": "한돈", "ctmeatYn": "N",
                    "skngStatNm": "박피",
                },
                "excluded_name_keywords": [
                    "슬라이스", "세절", "큐브", "구이용", "절단", "소포장",
                    "양념", "냉동", "수입",
                ],
            })
            market_item["review_note"] = "금천미트 목살 링크 상품은 API상 부위명 목심으로 일관 관리"
        elif market_item["item_id"] == "handon_picnic":
            market_item["lookup"].update({
                "method": "category",
                "category_no": (
                    "310110", "310204", "310304", "310404", "310704", "310804",
                    "311004", "810667", "811204", "812236", "812791", "815076",
                    "815975", "817605", "818265",
                ),
                "exact_filters": {
                    "homeNm": "국내산", "strgMthdGbNm": "냉장",
                    "plspartNm": "앞다리", "lsspeNm": "한돈", "ctmeatYn": "N",
                    "skngStatNm": "박피",
                },
                "excluded_name_keywords": [
                    "슬라이스", "제육", "세절", "큐브", "절단", "소포장",
                    "양념", "냉동", "수입",
                ],
            })
            market_item["review_note"] = "링크 상품군은 API상 앞다리 부위명으로 일관 관리"

# 최종 승인된 육우 채끝 2등급과 세절육 3개 품목입니다.
for market_category in TODAY_MARKET_CATEGORIES:
    for market_item in market_category["items"]:
        if market_item["item_id"] == "beef_cattle_striploin":
            market_item["display_status"] = "연동 준비 중"
            market_item["lookup"].update({
                "method": "category",
                "category_no": (
                    "210103", "210203", "210306", "210407", "210503", "210603",
                ),
                "exact_filters": {
                    "homeNm": "국내산", "strgMthdGbNm": "냉장",
                    "plspartNm": "채끝", "lsspeNm": "육우",
                    "lsprdGrdNm": "2", "ctmeatYn": "N",
                },
            })
            market_item["review_note"] = (
                "육우 채끝 대표 시세는 재고 수가 가장 많은 2등급 기준으로 설정"
            )
        elif market_item["item_id"] == "sliced_beef_belly":
            market_item["lookup"].update({
                "method": "category", "category_no": "813348",
                "exact_filters": {
                    "strgMthdGbNm": "냉동", "plspartNm": "삼겹양지",
                    "lsspeNm": "세절 수입산우", "ctmeatYn": "Y",
                },
                "required_name_keywords_any": ["슬라이스", "불고기/샤브"],
                "excluded_name_keywords": ["다짐육", "덩어리", "큐브", "양념"],
            })
            market_item["review_note"] = (
                "API상 공식 부위명은 삼겹양지. 슬라이스·불고기/샤브 세절 상품만 비교"
            )
        elif market_item["item_id"] == "sliced_pork_neck_picnic":
            market_item["lookup"].update({
                "method": "category", "category_no": "813367",
                "exact_filters": {
                    "strgMthdGbNm": "냉동", "plspartNm": "목전지",
                    "lsspeNm": "세절 수입산돈", "ctmeatYn": "Y",
                },
                "required_name_keywords_any": ["불고기", "슬라이스"],
                "excluded_name_keywords": [
                    "찌개용", "칼집", "다짐육", "큐브", "양념",
                ],
            })
            market_item["review_note"] = (
                "목전지 불고기·슬라이스는 두께·포장 무관 동일 세절 비교군으로 처리"
            )
        elif market_item["item_id"] == "sliced_beef_bulgogi":
            market_item["lookup"].update({
                "method": "category", "category_no": "813352",
                "exact_filters": {
                    "strgMthdGbNm": "냉동", "lsspeNm": "세절 수입산우",
                    "ctmeatYn": "Y",
                },
                "required_name_keywords_all": ["전각", "불고기"],
                "excluded_name_keywords": [
                    "다짐육", "양념", "큐브", "갈비살", "우삼겹",
                ],
            })
            market_item["review_note"] = (
                "상품명 전각·불고기 정확 포함 및 API 세절 수입산우 기준으로 비교"
            )


# 실제 카카오톡 상담 링크를 제공받기 전까지 QR을 생성하거나 표시하지 않습니다.
KAKAO_CHAT_URL = "https://open.kakao.com/o/sG85euyi"


# 2026-10-25 금천미트 getDispCtgList 및 dispGoodsList에서 확인한 신규 품목.
# 기존 17개 정의는 보존하며, 동일 카테고리의 복수 정확 필터는 별도 후보로 비교한다.
NEW_MARKET_ITEMS = [('hanwoo',
  {'item_id': 'hanwoo_tenderloin',
   'item_name': '안심',
   'lookup': {'method': 'category',
              'category_no': ('130101', '130201', '130301', '130401', '130501', '130701', '130801', '815887',
                              '817764', '819103', '812594', '140101', '817044', '140201', '140301', '140501',
                              '140601', '140701', '815917', '817794', '819135', '1501'),
              'goods_no': '',
              'search_keyword': '',
              'selection_policy': 'lowest_price_per_kg',
              'exact_filters': {'ctmeatYn': 'N', 'strgMthdGbNm': '냉장', 'homeNm': '국내산'},
              'filter_variants': [{'lsspeNm': '한우', 'plspartNm': '안심'}],
              'excluded_name_keywords': ['양념', '세절', '슬라이스', '큐브', '다짐육', '민찌', '돈가스', '돈까스', '대패', '불고기', '샤브',
                                         '찌개용', '구이용', '스테이크용', '소포장', '절단']},
   'display_status': '연동 준비 중',
   'origin': '국내산',
   'storage_status': '냉장',
   'image_url': '',
   'image_source': '',
   'image_status': '미연결'}),
 ('hanwoo',
  {'item_id': 'hanwoo_striploin',
   'item_name': '채끝',
   'lookup': {'method': 'category',
              'category_no': ('130103', '130203', '130303', '130403', '130503', '130703', '130803', '815886',
                              '817766', '819102', '812596', '140103', '817048', '140203', '140303', '140503',
                              '140603', '140703', '815916', '817796', '819133', '1503'),
              'goods_no': '',
              'search_keyword': '',
              'selection_policy': 'lowest_price_per_kg',
              'exact_filters': {'ctmeatYn': 'N', 'strgMthdGbNm': '냉장', 'homeNm': '국내산'},
              'filter_variants': [{'lsspeNm': '한우', 'plspartNm': '채끝'}],
              'excluded_name_keywords': ['양념', '세절', '슬라이스', '큐브', '다짐육', '민찌', '돈가스', '돈까스', '대패', '불고기', '샤브',
                                         '찌개용', '구이용', '스테이크용', '소포장', '절단']},
   'display_status': '연동 준비 중',
   'origin': '국내산',
   'storage_status': '냉장',
   'image_url': '',
   'image_source': '',
   'image_status': '미연결'}),
 ('hanwoo',
  {'item_id': 'hanwoo_blade',
   'item_name': '부채',
   'lookup': {'method': 'category',
              'category_no': ('130107', '130207', '130308', '130407', '130508', '130706', '130808', '815883',
                              '817769', '819098', '812600', '140107', '817052', '140207', '140308', '140508',
                              '140608', '140706', '815913', '817799', '819129', '1507'),
              'goods_no': '',
              'search_keyword': '',
              'selection_policy': 'lowest_price_per_kg',
              'exact_filters': {'ctmeatYn': 'N', 'strgMthdGbNm': '냉장', 'homeNm': '국내산'},
              'filter_variants': [{'lsspeNm': '한우', 'plspartNm': '부채살'}],
              'excluded_name_keywords': ['양념', '세절', '슬라이스', '큐브', '다짐육', '민찌', '돈가스', '돈까스', '대패', '불고기', '샤브',
                                         '찌개용', '구이용', '스테이크용', '소포장', '절단']},
   'display_status': '연동 준비 중',
   'origin': '국내산',
   'storage_status': '냉장',
   'image_url': '',
   'image_source': '',
   'image_status': '미연결'}),
 ('hanwoo',
  {'item_id': 'hanwoo_eye_round',
   'item_name': '홍두깨',
   'lookup': {'method': 'category',
              'category_no': ('130109', '130209', '130310', '130410', '130510', '130810', '815881', '817771',
                              '819096', '812602', '140109', '817054', '140209', '140310', '140511', '140610',
                              '815911', '817801', '819127', '1509'),
              'goods_no': '',
              'search_keyword': '',
              'selection_policy': 'lowest_price_per_kg',
              'exact_filters': {'ctmeatYn': 'N', 'strgMthdGbNm': '냉장', 'homeNm': '국내산'},
              'filter_variants': [{'lsspeNm': '한우', 'plspartNm': '홍두깨'}],
              'excluded_name_keywords': ['양념', '세절', '슬라이스', '큐브', '다짐육', '민찌', '돈가스', '돈까스', '대패', '불고기', '샤브',
                                         '찌개용', '구이용', '스테이크용', '소포장', '절단']},
   'display_status': '연동 준비 중',
   'origin': '국내산',
   'storage_status': '냉장',
   'image_url': '',
   'image_source': '',
   'image_status': '미연결'}),
 ('hanwoo',
  {'item_id': 'hanwoo_knuckle',
   'item_name': '설도',
   'lookup': {'method': 'category',
              'category_no': ('130110', '130210', '130311', '130411', '130512', '130708', '130812', '815879',
                              '812603', '140110', '817055', '140210', '140311', '140512', '140612', '140708',
                              '815909', '1510'),
              'goods_no': '',
              'search_keyword': '',
              'selection_policy': 'lowest_price_per_kg',
              'exact_filters': {'ctmeatYn': 'N', 'strgMthdGbNm': '냉장', 'homeNm': '국내산'},
              'filter_variants': [{'lsspeNm': '한우', 'plspartNm': '설도'}],
              'excluded_name_keywords': ['양념', '세절', '슬라이스', '큐브', '다짐육', '민찌', '돈가스', '돈까스', '대패', '불고기', '샤브',
                                         '찌개용', '구이용', '스테이크용', '소포장', '절단']},
   'display_status': '연동 준비 중',
   'origin': '국내산',
   'storage_status': '냉장',
   'image_url': '',
   'image_source': '',
   'image_status': '미연결'}),
 ('hanwoo',
  {'item_id': 'hanwoo_brisket_point',
   'item_name': '양지',
   'lookup': {'method': 'category',
              'category_no': ('130116', '130215', '130710', '130814', '815877', '817775', '819092', '812605',
                              '140116', '817057', '140215', '140710', '815907', '817805', '819123', '1516'),
              'goods_no': '',
              'search_keyword': '',
              'selection_policy': 'lowest_price_per_kg',
              'exact_filters': {'ctmeatYn': 'N', 'strgMthdGbNm': '냉장', 'homeNm': '국내산'},
              'filter_variants': [{'lsspeNm': '한우', 'plspartNm': '양지머리,치마양지'}],
              'excluded_name_keywords': ['양념', '세절', '슬라이스', '큐브', '다짐육', '민찌', '돈가스', '돈까스', '대패', '불고기', '샤브',
                                         '찌개용', '구이용', '스테이크용', '소포장', '절단']},
   'display_status': '연동 준비 중',
   'origin': '국내산',
   'storage_status': '냉장',
   'image_url': '',
   'image_source': '',
   'image_status': '미연결'}),
 ('hanwoo',
  {'item_id': 'hanwoo_skirt',
   'item_name': '치마',
   'lookup': {'method': 'category',
              'category_no': ('130112', '130213', '130315', '130416', '130514', '130712', '130815', '815873',
                              '817776', '819091', '812606', '140112', '817058', '140213', '140315', '140517',
                              '140614', '140712', '815902', '817806', '819122', '1512'),
              'goods_no': '',
              'search_keyword': '',
              'selection_policy': 'lowest_price_per_kg',
              'exact_filters': {'ctmeatYn': 'N', 'strgMthdGbNm': '냉장', 'homeNm': '국내산'},
              'filter_variants': [{'lsspeNm': '한우', 'plspartNm': '치마살'}],
              'excluded_name_keywords': ['양념', '세절', '슬라이스', '큐브', '다짐육', '민찌', '돈가스', '돈까스', '대패', '불고기', '샤브',
                                         '찌개용', '구이용', '스테이크용', '소포장', '절단']},
   'display_status': '연동 준비 중',
   'origin': '국내산',
   'storage_status': '냉장',
   'image_url': '',
   'image_source': '',
   'image_status': '미연결'}),
 ('hanwoo',
  {'item_id': 'hanwoo_shank',
   'item_name': '사태',
   'lookup': {'method': 'category',
              'category_no': ('130117', '130217', '130318', '130419', '130518', '130714', '130819', '815870',
                              '817779', '819087', '812610', '140117', '817062', '140217', '140318', '140520',
                              '140618', '140714', '815899', '817809', '819118', '1517'),
              'goods_no': '',
              'search_keyword': '',
              'selection_policy': 'lowest_price_per_kg',
              'exact_filters': {'ctmeatYn': 'N', 'strgMthdGbNm': '냉장', 'homeNm': '국내산'},
              'filter_variants': [{'lsspeNm': '한우', 'plspartNm': '사태'}],
              'excluded_name_keywords': ['양념', '세절', '슬라이스', '큐브', '다짐육', '민찌', '돈가스', '돈까스', '대패', '불고기', '샤브',
                                         '찌개용', '구이용', '스테이크용', '소포장', '절단']},
   'display_status': '연동 준비 중',
   'origin': '국내산',
   'storage_status': '냉장',
   'image_url': '',
   'image_source': '',
   'image_status': '미연결'}),
 ('hanwoo',
  {'item_id': 'hanwoo_outside_skirt',
   'item_name': '안창',
   'lookup': {'method': 'category',
              'category_no': ('130120', '130218', '130320', '130421', '130519', '130716', '815869', '817781',
                              '819086', '812613', '140120', '817065', '140218', '140320', '140522', '140619',
                              '140716', '815898', '817811', '819117', '1520'),
              'goods_no': '',
              'search_keyword': '',
              'selection_policy': 'lowest_price_per_kg',
              'exact_filters': {'ctmeatYn': 'N', 'strgMthdGbNm': '냉장', 'homeNm': '국내산'},
              'filter_variants': [{'lsspeNm': '한우', 'plspartNm': '안창살'}],
              'excluded_name_keywords': ['양념', '세절', '슬라이스', '큐브', '다짐육', '민찌', '돈가스', '돈까스', '대패', '불고기', '샤브',
                                         '찌개용', '구이용', '스테이크용', '소포장', '절단']},
   'display_status': '연동 준비 중',
   'origin': '국내산',
   'storage_status': '냉장',
   'image_url': '',
   'image_source': '',
   'image_status': '미연결'}),
 ('hanwoo',
  {'item_id': 'hanwoo_hanging',
   'item_name': '토시',
   'lookup': {'method': None,
              'category_no': ('130121', '814514', '130520', '816035', '817782', '819085', '812614', '140121',
                              '817066', '814524', '140620', '816025', '817812', '819116', '1521'),
              'goods_no': '',
              'search_keyword': '',
              'selection_policy': 'lowest_price_per_kg',
              'exact_filters': {'ctmeatYn': 'N', 'strgMthdGbNm': '냉장', 'homeNm': '국내산'},
              'filter_variants': [{'lsspeNm': '한우', 'plspartNm': '토시살'}],
              'excluded_name_keywords': ['양념', '세절', '슬라이스', '큐브', '다짐육', '민찌', '돈가스', '돈까스', '대패', '불고기', '샤브',
                                         '찌개용', '구이용', '스테이크용', '소포장', '절단']},
   'display_status': '미연결',
   'origin': '국내산',
   'storage_status': '냉장',
   'image_url': '',
   'image_source': '',
   'image_status': '미연결',
   'review_note': '판매 상품에 토시살 정확 일치 없음: 혼합 부위 또는 부위명 누락'}),
 ('beef_cattle',
  {'item_id': 'beef_cattle_tenderloin',
   'item_name': '냉장 안심',
   'lookup': {'method': 'category',
              'category_no': ('210101', '210201', '210301', '210401', '210501', '210601', '220101', '220201',
                              '220301', '220401', '220501', '230101', '818509'),
              'goods_no': '',
              'search_keyword': '',
              'selection_policy': 'lowest_price_per_kg',
              'exact_filters': {'ctmeatYn': 'N', 'strgMthdGbNm': '냉장', 'homeNm': '국내산'},
              'filter_variants': [{'lsspeNm': '육우', 'plspartNm': '안심'}],
              'excluded_name_keywords': ['양념', '세절', '슬라이스', '큐브', '다짐육', '민찌', '돈가스', '돈까스', '대패', '불고기', '샤브',
                                         '찌개용', '구이용', '스테이크용', '소포장', '절단']},
   'display_status': '연동 준비 중',
   'origin': '국내산',
   'storage_status': '냉장',
   'image_url': '',
   'image_source': '',
   'image_status': '미연결'}),
 ('beef_cattle',
  {'item_id': 'beef_cattle_blade',
   'item_name': '냉장 부채살',
   'lookup': {'method': 'category',
              'category_no': ('210107', '210207', '210310', '210412', '210506', '210607', '220107', '220210',
                              '220313', '220406', '220507'),
              'goods_no': '',
              'search_keyword': '',
              'selection_policy': 'lowest_price_per_kg',
              'exact_filters': {'ctmeatYn': 'N', 'strgMthdGbNm': '냉장', 'homeNm': '국내산'},
              'filter_variants': [{'lsspeNm': '육우', 'plspartNm': '부채살'}],
              'excluded_name_keywords': ['양념', '세절', '슬라이스', '큐브', '다짐육', '민찌', '돈가스', '돈까스', '대패', '불고기', '샤브',
                                         '찌개용', '구이용', '스테이크용', '소포장', '절단']},
   'display_status': '연동 준비 중',
   'origin': '국내산',
   'storage_status': '냉장',
   'image_url': '',
   'image_source': '',
   'image_status': '미연결'}),
 ('handon',
  {'item_id': 'handon_skin_belly',
   'item_name': '미박삼겹살(오겹)',
   'lookup': {'method': 'category',
              'category_no': ('813744', '813764', '310106', '310107', '310202', '310302', '818264', '815078',
                              '816087', '810666', '810677', '817595', '816744', '816764', '311101', '311002',
                              '811184', '815964', '310802', '812793', '310402'),
              'goods_no': '',
              'search_keyword': '',
              'selection_policy': 'lowest_price_per_kg',
              'exact_filters': {'ctmeatYn': 'N', 'strgMthdGbNm': '냉장', 'homeNm': '국내산', 'skngStatNm': '미박'},
              'filter_variants': [{'lsspeNm': '한돈', 'plspartNm': '미박삼겹'},
                                  {'lsspeNm': '한돈', 'plspartNm': '더좋은미박삼겹'}],
              'excluded_name_keywords': ['양념', '세절', '슬라이스', '큐브', '다짐육', '민찌', '돈가스', '돈까스', '대패', '불고기', '샤브',
                                         '찌개용', '구이용', '스테이크용', '소포장', '절단']},
   'display_status': '연동 준비 중',
   'origin': '국내산',
   'storage_status': '냉장',
   'image_url': '',
   'image_source': '',
   'image_status': '미연결'}),
 ('handon',
  {'item_id': 'handon_loin',
   'item_name': '등심',
   'lookup': {'method': 'category',
              'category_no': ('310115', '813734', '310208', '310308', '818268', '818334', '815065', '818154',
                              '810707', '817608', '817564', '311105', '311007', '811207', '811205', '815985',
                              '310807', '812787', '310409'),
              'goods_no': '',
              'search_keyword': '',
              'selection_policy': 'lowest_price_per_kg',
              'exact_filters': {'ctmeatYn': 'N', 'strgMthdGbNm': '냉장', 'homeNm': '국내산'},
              'filter_variants': [{'lsspeNm': '한돈', 'plspartNm': '등심'}, {'lsspeNm': '한돈', 'plspartNm': '등심MM'},
                                  {'lsspeNm': '한돈', 'plspartNm': '지방등심'}],
              'excluded_name_keywords': ['양념', '세절', '슬라이스', '큐브', '다짐육', '민찌', '돈가스', '돈까스', '대패', '불고기', '샤브',
                                         '찌개용', '구이용', '스테이크용', '소포장', '절단']},
   'display_status': '연동 준비 중',
   'origin': '국내산',
   'storage_status': '냉장',
   'image_url': '',
   'image_source': '',
   'image_status': '미연결'}),
 ('handon',
  {'item_id': 'handon_tenderloin',
   'item_name': '안심',
   'lookup': {'method': 'category',
              'category_no': ('310116', '310213', '310313', '818275', '815071', '818164', '810964', '817609',
                              '818684', '311106', '311008', '811234', '815994', '310808', '812789', '310410'),
              'goods_no': '',
              'search_keyword': '',
              'selection_policy': 'lowest_price_per_kg',
              'exact_filters': {'ctmeatYn': 'N', 'strgMthdGbNm': '냉장', 'homeNm': '국내산'},
              'filter_variants': [{'lsspeNm': '한돈', 'plspartNm': '안심'}, {'lsspeNm': '한돈', 'plspartNm': '안심S'}],
              'excluded_name_keywords': ['양념', '세절', '슬라이스', '큐브', '다짐육', '민찌', '돈가스', '돈까스', '대패', '불고기', '샤브',
                                         '찌개용', '구이용', '스테이크용', '소포장', '절단']},
   'display_status': '연동 준비 중',
   'origin': '국내산',
   'storage_status': '냉장',
   'image_url': '',
   'image_source': '',
   'image_status': '미연결'}),
 ('handon',
  {'item_id': 'handon_jowl',
   'item_name': '항정',
   'lookup': {'method': 'category',
              'category_no': ('310119', '310210', '310310', '818277', '815068', '810720', '817610', '818864',
                              '311108', '311011', '811254', '815995', '310811', '813004', '310413'),
              'goods_no': '',
              'search_keyword': '',
              'selection_policy': 'lowest_price_per_kg',
              'exact_filters': {'ctmeatYn': 'N', 'strgMthdGbNm': '냉장', 'homeNm': '국내산'},
              'filter_variants': [{'lsspeNm': '한돈', 'plspartNm': '항정'}],
              'excluded_name_keywords': ['양념', '세절', '슬라이스', '큐브', '다짐육', '민찌', '돈가스', '돈까스', '대패', '불고기', '샤브',
                                         '찌개용', '구이용', '스테이크용', '소포장', '절단']},
   'display_status': '연동 준비 중',
   'origin': '국내산',
   'storage_status': '냉장',
   'image_url': '',
   'image_source': '',
   'image_status': '미연결'}),
 ('handon',
  {'item_id': 'handon_skirt',
   'item_name': '갈매기',
   'lookup': {'method': 'category',
              'category_no': ('310121', '310212', '310312', '818278', '815066', '810718', '817611', '818855',
                              '311013', '811265', '816015', '310813', '812785', '310415'),
              'goods_no': '',
              'search_keyword': '',
              'selection_policy': 'lowest_price_per_kg',
              'exact_filters': {'ctmeatYn': 'N', 'strgMthdGbNm': '냉장', 'homeNm': '국내산'},
              'filter_variants': [{'lsspeNm': '한돈', 'plspartNm': '갈매기'}],
              'excluded_name_keywords': ['양념', '세절', '슬라이스', '큐브', '다짐육', '민찌', '돈가스', '돈까스', '대패', '불고기', '샤브',
                                         '찌개용', '구이용', '스테이크용', '소포장', '절단']},
   'display_status': '연동 준비 중',
   'origin': '국내산',
   'storage_status': '냉장',
   'image_url': '',
   'image_source': '',
   'image_status': '미연결'}),
 ('handon',
  {'item_id': 'handon_back',
   'item_name': '등심덧살(가브리)',
   'lookup': {'method': 'category',
              'category_no': ('310120', '310211', '310311', '818285', '815067', '810719', '817612', '818874',
                              '311012', '811245', '816014', '310812', '812786', '310414'),
              'goods_no': '',
              'search_keyword': '',
              'selection_policy': 'lowest_price_per_kg',
              'exact_filters': {'ctmeatYn': 'N', 'strgMthdGbNm': '냉장', 'homeNm': '국내산'},
              'filter_variants': [{'lsspeNm': '한돈', 'plspartNm': '등심덧살'}],
              'excluded_name_keywords': ['양념', '세절', '슬라이스', '큐브', '다짐육', '민찌', '돈가스', '돈까스', '대패', '불고기', '샤브',
                                         '찌개용', '구이용', '스테이크용', '소포장', '절단']},
   'display_status': '연동 준비 중',
   'origin': '국내산',
   'storage_status': '냉장',
   'image_url': '',
   'image_source': '',
   'image_status': '미연결'}),
 ('imported_beef',
  {'item_id': 'imported_beef_chuck_eye',
   'item_name': '냉장 알목심',
   'lookup': {'method': 'category',
              'category_no': ('410112', '814087', '814117', '814147', '812844', '814326', '812416', '816344',
                              '816864'),
              'goods_no': '',
              'search_keyword': '',
              'selection_policy': 'lowest_price_per_kg',
              'exact_filters': {'ctmeatYn': 'N', 'strgMthdGbNm': '냉장'},
              'filter_variants': [{'lsspeNm': '수입우', 'plspartNm': '알목심'},
                                  {'lsspeNm': '낱개 수입산우', 'plspartNm': '알목심'}],
              'excluded_name_keywords': ['양념', '세절', '슬라이스', '큐브', '다짐육', '민찌', '돈가스', '돈까스', '대패', '불고기', '샤브',
                                         '찌개용', '구이용', '스테이크용', '소포장', '절단']},
   'display_status': '연동 준비 중',
   'origin': '',
   'storage_status': '냉장',
   'image_url': '',
   'image_source': '',
   'image_status': '미연결'}),
 ('imported_beef',
  {'item_id': 'imported_beef_short_rib',
   'item_name': '냉장 진갈비살',
   'lookup': {'method': 'category',
              'category_no': ('410113', '814088', '410217', '813908', '816690', '812406'),
              'goods_no': '',
              'search_keyword': '',
              'selection_policy': 'lowest_price_per_kg',
              'exact_filters': {'ctmeatYn': 'N', 'strgMthdGbNm': '냉장'},
              'filter_variants': [{'lsspeNm': '수입우', 'plspartNm': '진갈비'},
                                  {'lsspeNm': '낱개 수입산우', 'plspartNm': '진갈비'}],
              'excluded_name_keywords': ['양념', '세절', '슬라이스', '큐브', '다짐육', '민찌', '돈가스', '돈까스', '대패', '불고기', '샤브',
                                         '찌개용', '구이용', '스테이크용', '소포장', '절단']},
   'display_status': '연동 준비 중',
   'origin': '',
   'storage_status': '냉장',
   'image_url': '',
   'image_source': '',
   'image_status': '미연결'}),
 ('imported_beef',
  {'item_id': 'imported_beef_emperor',
   'item_name': '냉장 황제늑간',
   'lookup': {'method': 'category',
              'category_no': ('410119', '814094', '814124', '814154', '815244', '812504'),
              'goods_no': '',
              'search_keyword': '',
              'selection_policy': 'lowest_price_per_kg',
              'exact_filters': {'ctmeatYn': 'N', 'strgMthdGbNm': '냉장'},
              'filter_variants': [{'lsspeNm': '수입우', 'plspartNm': '황제늑간'},
                                  {'lsspeNm': '낱개 수입산우', 'plspartNm': '황제늑간'}],
              'excluded_name_keywords': ['양념', '세절', '슬라이스', '큐브', '다짐육', '민찌', '돈가스', '돈까스', '대패', '불고기', '샤브',
                                         '찌개용', '구이용', '스테이크용', '소포장', '절단']},
   'display_status': '연동 준비 중',
   'origin': '',
   'storage_status': '냉장',
   'image_url': '',
   'image_source': '',
   'image_status': '미연결'}),
 ('imported_beef',
  {'item_id': 'imported_beef_chuck_flap',
   'item_name': '냉장 살치',
   'lookup': {'method': 'category',
              'category_no': ('410107', '814111', '814141', '410209', '813893', '814367', '816675', '812418',
                              '812951'),
              'goods_no': '',
              'search_keyword': '',
              'selection_policy': 'lowest_price_per_kg',
              'exact_filters': {'ctmeatYn': 'N', 'strgMthdGbNm': '냉장'},
              'filter_variants': [{'lsspeNm': '수입우', 'plspartNm': '살치살'},
                                  {'lsspeNm': '낱개 수입산우', 'plspartNm': '살치살'}],
              'excluded_name_keywords': ['양념', '세절', '슬라이스', '큐브', '다짐육', '민찌', '돈가스', '돈까스', '대패', '불고기', '샤브',
                                         '찌개용', '구이용', '스테이크용', '소포장', '절단']},
   'display_status': '연동 준비 중',
   'origin': '',
   'storage_status': '냉장',
   'image_url': '',
   'image_source': '',
   'image_status': '미연결'}),
 ('imported_beef',
  {'item_id': 'imported_beef_la_rib',
   'item_name': '냉동 LA갈비',
   'lookup': {'method': 'category',
              'category_no': ('420102', '810854', '812457', '816195'),
              'goods_no': '',
              'search_keyword': '',
              'selection_policy': 'lowest_price_per_kg',
              'exact_filters': {'ctmeatYn': 'N', 'strgMthdGbNm': '냉동'},
              'filter_variants': [{'lsspeNm': '수입우', 'plspartNm': 'LA갈비'},
                                  {'lsspeNm': '낱개 수입산우', 'plspartNm': 'LA갈비'}],
              'excluded_name_keywords': ['양념', '세절', '슬라이스', '큐브', '다짐육', '민찌', '돈가스', '돈까스', '대패', '불고기', '샤브',
                                         '찌개용', '구이용', '스테이크용', '소포장']},
   'display_status': '연동 준비 중',
   'origin': '',
   'storage_status': '냉동',
   'image_url': '',
   'image_source': '',
   'image_status': '미연결'}),
 ('imported_beef',
  {'item_id': 'imported_beef_clod',
   'item_name': '냉동 볼라전각(앞다리)',
   'lookup': {'method': 'category',
              'category_no': ('420107', '420124', '420210', '420233', '420310', '420311', '810847', '813570',
                              '812447'),
              'goods_no': '',
              'search_keyword': '',
              'selection_policy': 'lowest_price_per_kg',
              'exact_filters': {'ctmeatYn': 'N', 'strgMthdGbNm': '냉동'},
              'filter_variants': [{'lsspeNm': '수입우', 'plspartNm': '볼라전각'}, {'lsspeNm': '수입우', 'plspartNm': '전각'},
                                  {'lsspeNm': '낱개 수입산우', 'plspartNm': '볼라전각'},
                                  {'lsspeNm': '낱개 수입산우', 'plspartNm': '전각'}],
              'excluded_name_keywords': ['양념', '세절', '슬라이스', '큐브', '다짐육', '민찌', '돈가스', '돈까스', '대패', '불고기', '샤브',
                                         '찌개용', '구이용', '스테이크용', '소포장', '절단']},
   'display_status': '연동 준비 중',
   'origin': '',
   'storage_status': '냉동',
   'image_url': '',
   'image_source': '',
   'image_status': '미연결'}),
 ('imported_beef',
  {'item_id': 'imported_beef_tendon',
   'item_name': '냉동 스지',
   'lookup': {'method': 'category',
              'category_no': ('420119', '420105', '420222', '420225', '420223', '420305', '814954'),
              'goods_no': '',
              'search_keyword': '',
              'selection_policy': 'lowest_price_per_kg',
              'exact_filters': {'ctmeatYn': 'N', 'strgMthdGbNm': '냉동'},
              'filter_variants': [{'lsspeNm': '수입우', 'plspartNm': '스지'},
                                  {'lsspeNm': '낱개 수입산우', 'plspartNm': '스지'}],
              'excluded_name_keywords': ['양념', '세절', '슬라이스', '큐브', '다짐육', '민찌', '돈가스', '돈까스', '대패', '불고기', '샤브',
                                         '찌개용', '구이용', '스테이크용', '소포장', '절단']},
   'display_status': '연동 준비 중',
   'origin': '',
   'storage_status': '냉동',
   'image_url': '',
   'image_source': '',
   'image_status': '미연결'}),
 ('imported_beef',
  {'item_id': 'imported_beef_brisket',
   'item_name': '냉동 차돌양지',
   'lookup': {'method': 'category',
              'category_no': ('420127', '420235', '420312', '810864', '815314', '812461', '816224'),
              'goods_no': '',
              'search_keyword': '',
              'selection_policy': 'lowest_price_per_kg',
              'exact_filters': {'ctmeatYn': 'N', 'strgMthdGbNm': '냉동'},
              'filter_variants': [{'lsspeNm': '수입우', 'plspartNm': '차돌양지'},
                                  {'lsspeNm': '낱개 수입산우', 'plspartNm': '차돌양지'}],
              'excluded_name_keywords': ['양념', '세절', '슬라이스', '큐브', '다짐육', '민찌', '돈가스', '돈까스', '대패', '불고기', '샤브',
                                         '찌개용', '구이용', '스테이크용', '소포장', '절단']},
   'display_status': '연동 준비 중',
   'origin': '',
   'storage_status': '냉동',
   'image_url': '',
   'image_source': '',
   'image_status': '미연결'}),
 ('imported_beef',
  {'item_id': 'imported_beef_brisket_point',
   'item_name': '냉동 차돌박이',
   'lookup': {'method': 'category',
              'category_no': ('420126', '420236', '812460', '816347'),
              'goods_no': '',
              'search_keyword': '',
              'selection_policy': 'lowest_price_per_kg',
              'exact_filters': {'ctmeatYn': 'N', 'strgMthdGbNm': '냉동'},
              'filter_variants': [{'lsspeNm': '수입우', 'plspartNm': '차돌박이'},
                                  {'lsspeNm': '낱개 수입산우', 'plspartNm': '차돌박이'}],
              'excluded_name_keywords': ['양념', '세절', '슬라이스', '큐브', '다짐육', '민찌', '돈가스', '돈까스', '대패', '불고기', '샤브',
                                         '찌개용', '구이용', '스테이크용', '소포장', '절단']},
   'display_status': '연동 준비 중',
   'origin': '',
   'storage_status': '냉동',
   'image_url': '',
   'image_source': '',
   'image_status': '미연결'}),
 ('imported_beef',
  {'item_id': 'imported_beef_plate',
   'item_name': '냉동 삼겹양지',
   'lookup': {'method': 'category',
              'category_no': ('420115', '420219', '814934', '813567', '816634', '816345'),
              'goods_no': '',
              'search_keyword': '',
              'selection_policy': 'lowest_price_per_kg',
              'exact_filters': {'ctmeatYn': 'N', 'strgMthdGbNm': '냉동'},
              'filter_variants': [{'lsspeNm': '수입우', 'plspartNm': '삼겹양지'},
                                  {'lsspeNm': '낱개 수입산우', 'plspartNm': '삼겹양지'}],
              'excluded_name_keywords': ['양념', '세절', '슬라이스', '큐브', '다짐육', '민찌', '돈가스', '돈까스', '대패', '불고기', '샤브',
                                         '찌개용', '구이용', '스테이크용', '소포장', '절단']},
   'display_status': '연동 준비 중',
   'origin': '',
   'storage_status': '냉동',
   'image_url': '',
   'image_source': '',
   'image_status': '미연결'}),
 ('imported_beef',
  {'item_id': 'imported_beef_intestine',
   'item_name': '냉동 곱창',
   'lookup': {'method': 'category',
              'category_no': ('420201', '420301', '812184', '816194'),
              'goods_no': '',
              'search_keyword': '',
              'selection_policy': 'lowest_price_per_kg',
              'exact_filters': {'ctmeatYn': 'N', 'strgMthdGbNm': '냉동'},
              'filter_variants': [{'lsspeNm': '수입우', 'plspartNm': '곱창'},
                                  {'lsspeNm': '낱개 수입산우', 'plspartNm': '곱창'}],
              'excluded_name_keywords': ['양념', '세절', '슬라이스', '큐브', '다짐육', '민찌', '돈가스', '돈까스', '대패', '불고기', '샤브',
                                         '찌개용', '구이용', '스테이크용', '소포장', '절단']},
   'display_status': '연동 준비 중',
   'origin': '',
   'storage_status': '냉동',
   'image_url': '',
   'image_source': '',
   'image_status': '미연결'}),
 ('imported_pork',
  {'item_id': 'imported_pork_chilled_belly',
   'item_name': '냉장 삼겹살',
   'lookup': {'method': 'category',
              'category_no': ('510201', '814274', '814284', '814276', '510101', '814278', '819194', '818547'),
              'goods_no': '',
              'search_keyword': '',
              'selection_policy': 'lowest_price_per_kg',
              'exact_filters': {'ctmeatYn': 'N', 'strgMthdGbNm': '냉장'},
              'filter_variants': [{'lsspeNm': '수입돈', 'plspartNm': '삼겹'},
                                  {'lsspeNm': '낱개 수입산돈', 'plspartNm': '삼겹'}],
              'excluded_name_keywords': ['양념', '세절', '슬라이스', '큐브', '다짐육', '민찌', '돈가스', '돈까스', '대패', '불고기', '샤브',
                                         '찌개용', '구이용', '스테이크용', '소포장', '절단']},
   'display_status': '연동 준비 중',
   'origin': '',
   'storage_status': '냉장',
   'image_url': '',
   'image_source': '',
   'image_status': '미연결'}),
 ('imported_pork',
  {'item_id': 'imported_pork_chilled_neck',
   'item_name': '냉장 목살',
   'lookup': {'method': 'category',
              'category_no': ('510202', '814275', '814285', '814277', '510102', '814279', '819195', '818539',
                              '818824'),
              'goods_no': '',
              'search_keyword': '',
              'selection_policy': 'lowest_price_per_kg',
              'exact_filters': {'ctmeatYn': 'N', 'strgMthdGbNm': '냉장'},
              'filter_variants': [{'lsspeNm': '수입돈', 'plspartNm': '목심'},
                                  {'lsspeNm': '낱개 수입산돈', 'plspartNm': '목심'}],
              'excluded_name_keywords': ['양념', '세절', '슬라이스', '큐브', '다짐육', '민찌', '돈가스', '돈까스', '대패', '불고기', '샤브',
                                         '찌개용', '구이용', '스테이크용', '소포장', '절단']},
   'display_status': '연동 준비 중',
   'origin': '',
   'storage_status': '냉장',
   'image_url': '',
   'image_source': '',
   'image_status': '미연결'}),
 ('imported_pork',
  {'item_id': 'imported_pork_back',
   'item_name': '냉동 가브리',
   'lookup': {'method': 'category',
              'category_no': ('520301', '520401', '814994', '816114', '818551'),
              'goods_no': '',
              'search_keyword': '',
              'selection_policy': 'lowest_price_per_kg',
              'exact_filters': {'ctmeatYn': 'N', 'strgMthdGbNm': '냉동'},
              'filter_variants': [{'lsspeNm': '수입돈', 'plspartNm': '가브리살'},
                                  {'lsspeNm': '낱개 수입산돈', 'plspartNm': '가브리살'}],
              'excluded_name_keywords': ['양념', '세절', '슬라이스', '큐브', '다짐육', '민찌', '돈가스', '돈까스', '대패', '불고기', '샤브',
                                         '찌개용', '구이용', '스테이크용', '소포장', '절단']},
   'display_status': '연동 준비 중',
   'origin': '',
   'storage_status': '냉동',
   'image_url': '',
   'image_source': '',
   'image_status': '미연결'}),
 ('imported_pork',
  {'item_id': 'imported_pork_rib',
   'item_name': '냉동 갈비',
   'lookup': {'method': 'category',
              'category_no': ('520103', '520306', '520403', '812874', '812895', '812883', '520201', '819174',
                              '813204', '818541'),
              'goods_no': '',
              'search_keyword': '',
              'selection_policy': 'lowest_price_per_kg',
              'exact_filters': {'ctmeatYn': 'N', 'strgMthdGbNm': '냉동'},
              'filter_variants': [{'lsspeNm': '수입돈', 'plspartNm': '돼지갈비'},
                                  {'lsspeNm': '낱개 수입산돈', 'plspartNm': '돼지갈비'}],
              'excluded_name_keywords': ['양념', '세절', '슬라이스', '큐브', '다짐육', '민찌', '돈가스', '돈까스', '대패', '불고기', '샤브',
                                         '찌개용', '구이용', '스테이크용', '소포장', '절단']},
   'display_status': '연동 준비 중',
   'origin': '',
   'storage_status': '냉동',
   'image_url': '',
   'image_source': '',
   'image_status': '미연결'}),
 ('imported_pork',
  {'item_id': 'imported_pork_loin_rib',
   'item_name': '냉동 로인립',
   'lookup': {'method': 'category',
              'category_no': ('520104', '520105', '816514', '520308', '816524', '520406', '813584', '817724',
                              '812884', '816534', '818540', '816295', '816274', '818084'),
              'goods_no': '',
              'search_keyword': '',
              'selection_policy': 'lowest_price_per_kg',
              'exact_filters': {'ctmeatYn': 'N', 'strgMthdGbNm': '냉동'},
              'filter_variants': [{'lsspeNm': '수입돈', 'plspartNm': '로인립'}, {'lsspeNm': '수입돈', 'plspartNm': '모돈로인립'},
                                  {'lsspeNm': '낱개 수입산돈', 'plspartNm': '로인립'},
                                  {'lsspeNm': '낱개 수입산돈', 'plspartNm': '모돈로인립'}],
              'excluded_name_keywords': ['양념', '세절', '슬라이스', '큐브', '다짐육', '민찌', '돈가스', '돈까스', '대패', '불고기', '샤브',
                                         '찌개용', '구이용', '스테이크용', '소포장', '절단']},
   'display_status': '연동 준비 중',
   'origin': '',
   'storage_status': '냉동',
   'image_url': '',
   'image_source': '',
   'image_status': '미연결'}),
 ('imported_pork',
  {'item_id': 'imported_pork_cheek',
   'item_name': '냉동 뽈살',
   'lookup': {'method': 'category',
              'category_no': ('520110',),
              'goods_no': '',
              'search_keyword': '',
              'selection_policy': 'lowest_price_per_kg',
              'exact_filters': {'ctmeatYn': 'N', 'strgMthdGbNm': '냉동'},
              'filter_variants': [{'lsspeNm': '수입돈', 'plspartNm': '뽈살'},
                                  {'lsspeNm': '낱개 수입산돈', 'plspartNm': '뽈살'}],
              'excluded_name_keywords': ['양념', '세절', '슬라이스', '큐브', '다짐육', '민찌', '돈가스', '돈까스', '대패', '불고기', '샤브',
                                         '찌개용', '구이용', '스테이크용', '소포장', '절단']},
   'display_status': '연동 준비 중',
   'origin': '',
   'storage_status': '냉동',
   'image_url': '',
   'image_source': '',
   'image_status': '미연결'}),
 ('imported_pork',
  {'item_id': 'imported_pork_spare_rib',
   'item_name': '냉동 스페어립',
   'lookup': {'method': 'category',
              'category_no': ('520112', '817674', '520328', '816285', '818094'),
              'goods_no': '',
              'search_keyword': '',
              'selection_policy': 'lowest_price_per_kg',
              'exact_filters': {'ctmeatYn': 'N', 'strgMthdGbNm': '냉동'},
              'filter_variants': [{'lsspeNm': '수입돈', 'plspartNm': '스페어립'},
                                  {'lsspeNm': '낱개 수입산돈', 'plspartNm': '스페어립'}],
              'excluded_name_keywords': ['양념', '세절', '슬라이스', '큐브', '다짐육', '민찌', '돈가스', '돈까스', '대패', '불고기', '샤브',
                                         '찌개용', '구이용', '스테이크용', '소포장', '절단']},
   'display_status': '연동 준비 중',
   'origin': '',
   'storage_status': '냉동',
   'image_url': '',
   'image_source': '',
   'image_status': '미연결'}),
 ('imported_pork',
  {'item_id': 'imported_pork_hock',
   'item_name': '냉동 학',
   'lookup': {'method': 'category',
              'category_no': ('815854', '520305', '812894', '816304'),
              'goods_no': '',
              'search_keyword': '',
              'selection_policy': 'lowest_price_per_kg',
              'exact_filters': {'ctmeatYn': 'N', 'strgMthdGbNm': '냉동'},
              'filter_variants': [{'lsspeNm': '수입돈', 'plspartNm': '돈학'},
                                  {'lsspeNm': '낱개 수입산돈', 'plspartNm': '돈학'}],
              'excluded_name_keywords': ['양념', '세절', '슬라이스', '큐브', '다짐육', '민찌', '돈가스', '돈까스', '대패', '불고기', '샤브',
                                         '찌개용', '구이용', '스테이크용', '소포장', '절단']},
   'display_status': '연동 준비 중',
   'origin': '',
   'storage_status': '냉동',
   'image_url': '',
   'image_source': '',
   'image_status': '미연결'}),
 ('imported_pork',
  {'item_id': 'imported_pork_jowl',
   'item_name': '냉동 항정살',
   'lookup': {'method': 'category',
              'category_no': ('818354', '520334', '520338', '520418', '520421', '817734', '813244', '814406',
                              '818844', '818543', '818826'),
              'goods_no': '',
              'search_keyword': '',
              'selection_policy': 'lowest_price_per_kg',
              'exact_filters': {'ctmeatYn': 'N', 'strgMthdGbNm': '냉동'},
              'filter_variants': [{'lsspeNm': '수입돈', 'plspartNm': '항정'}, {'lsspeNm': '수입돈', 'plspartNm': '작업항정'},
                                  {'lsspeNm': '낱개 수입산돈', 'plspartNm': '항정'},
                                  {'lsspeNm': '낱개 수입산돈', 'plspartNm': '작업항정'}],
              'excluded_name_keywords': ['양념', '세절', '슬라이스', '큐브', '다짐육', '민찌', '돈가스', '돈까스', '대패', '불고기', '샤브',
                                         '찌개용', '구이용', '스테이크용', '소포장', '절단']},
   'display_status': '연동 준비 중',
   'origin': '',
   'storage_status': '냉동',
   'image_url': '',
   'image_source': '',
   'image_status': '미연결'}),
 ('sliced_meat',
  {'item_id': 'hanwoo_mince',
   'item_name': '한우 냉동 잡육(민찌/다짐육)',
   'lookup': {'method': 'category',
              'category_no': ('813323', '813338', '813484'),
              'goods_no': '',
              'search_keyword': '',
              'selection_policy': 'lowest_price_per_kg',
              'exact_filters': {'ctmeatYn': 'Y', 'strgMthdGbNm': '냉동', 'homeNm': '국내산'},
              'filter_variants': [{'lsspeNm': '세절 국내산우', 'plspartNm': '잡육'}],
              'required_name_keywords_all': ['한우'],
              'required_name_keywords_any': ['민찌', '다짐육'],
              'excluded_name_keywords': ['양념', '부채']},
   'display_status': '연동 준비 중',
   'origin': '국내산',
   'storage_status': '냉동',
   'image_url': '',
   'image_source': '',
   'image_status': '미연결'}),
 ('sliced_meat',
  {'item_id': 'hanwoo_fat',
   'item_name': '한우 두태지방',
   'lookup': {'method': 'category',
              'category_no': ('817184', '817194'),
              'goods_no': '',
              'search_keyword': '',
              'selection_policy': 'lowest_price_per_kg',
              'exact_filters': {'ctmeatYn': 'Y', 'homeNm': '국내산'},
              'filter_variants': [{'lsspeNm': '세절 국내산우', 'plspartNm': '지방'}],
              'required_name_keywords_all': ['한우', '두태지방']},
   'display_status': '연동 준비 중',
   'origin': '국내산',
   'storage_status': '',
   'image_url': '',
   'image_source': '',
   'image_status': '미연결'}),
 ('sliced_meat',
  {'item_id': 'imported_beef_mince',
   'item_name': '수입 전각/앞다리(민찌/다짐육)',
   'lookup': {'method': 'category',
              'category_no': ('813352', '813428', '813487'),
              'goods_no': '',
              'search_keyword': '',
              'selection_policy': 'lowest_price_per_kg',
              'exact_filters': {'ctmeatYn': 'Y'},
              'filter_variants': [{'lsspeNm': '세절 수입산우', 'plspartNm': '전각'},
                                  {'lsspeNm': '세절 수입산우', 'plspartNm': '앞다리'},
                                  {'lsspeNm': '세절 수입산우', 'plspartNm': '볼라전각'}],
              'required_name_keywords_all': [],
              'required_name_keywords_any': ['민찌', '다짐육'],
              'excluded_name_keywords': ['양념', '부채']},
   'display_status': '연동 준비 중',
   'origin': '',
   'storage_status': '',
   'image_url': '',
   'image_source': '',
   'image_status': '미연결'})]
for _category_id, _item in NEW_MARKET_ITEMS:
    next(group for group in TODAY_MARKET_CATEGORIES
         if group["category_id"] == _category_id)["items"].append(_item)
next(group for group in TODAY_MARKET_CATEGORIES
     if group["category_id"] == "sliced_meat")["category_name"] = "세절/기타"


def get_today_market_report(category_id=None, include_live_prices=False):
    """종합 또는 선택 카테고리 단가표 구조를 선택적으로 실시간 가격과 합친다."""
    if category_id is None:
        report = {
            "report_id": "all",
            "title": "오늘의 축산물 실시간 단가",
            "groups": deepcopy(TODAY_MARKET_CATEGORIES),
        }
    else:
        report = None
        for category in TODAY_MARKET_CATEGORIES:
            if category["category_id"] != category_id:
                continue
            report = {
                "report_id": category_id,
                "title": f'{category["category_name"]} 실시간 단가',
                "groups": [deepcopy(category)],
            }
            break
    if report is None or not include_live_prices:
        return report

    sources = []
    connected_items = []
    for group in report["groups"]:
        for item in group["items"]:
            lookup = item["lookup"]
            method = lookup.get("method")
            if method not in {"category", "goods", "keyword"}:
                continue
            source = {
                "type": method,
                "label": item["item_name"],
                "selection_policy": lookup["selection_policy"],
                "exact_filters": lookup.get("exact_filters", {}),
                "excluded_name_keywords": lookup.get("excluded_name_keywords", []),
                "required_name_keywords_any": lookup.get("required_name_keywords_any", []),
                "required_name_keywords_all": lookup.get("required_name_keywords_all", []),
            }
            if method == "category":
                source["category_no"] = lookup["category_no"]
            elif method == "goods":
                source["goods_no"] = lookup["goods_no"]
            else:
                source["search_keyword"] = lookup["search_keyword"]
            for variant in lookup.get("filter_variants", [{}]):
                sources.append({**source, "exact_filters": {**source["exact_filters"], **variant}})
                connected_items.append(item)

    if not sources:
        return report

    from market_api import get_market_prices

    result = get_market_prices(sources)
    # input_order is the source identity: category numbers alone collide across filters.
    products_by_item = {}
    for product in result["products"]:
        item_id = connected_items[product["input_order"]]["item_id"]
        previous = products_by_item.get(item_id)
        if previous is None or product["kg_price"] < previous["kg_price"]:
            products_by_item[item_id] = product
    for item in {item["item_id"]: item for item in connected_items}.values():
        product = products_by_item.get(item["item_id"])
        if product is None:
            item["display_status"] = "현재 조회 불가"
            continue
        item.update({
            "kg_price": product.get("kg_price_rounded", round(product["kg_price"])),
            "goods_no": product["goods_no"],
            "goods_name": product["goods_name"],
            "grade": product["grade"],
            "livestock": product.get("livestock", ""),
            "part": product.get("part", ""),
            "processing_status": product.get("processing_status", ""),
            "ctmeat_yn": product.get("ctmeat_yn", ""),
            "brand": product["brand"],
            "origin": product.get("origin") or item.get("origin", ""),
            "storage_status": product.get("storage_status") or item.get("storage_status", ""),
            "image_url": product.get("image_url", ""),
            "image_source": product.get("image_source", ""),
            "image_status": product.get("image_status", "미연결"),
            "sale_price": product["sale_price"],
            "weight_kg": product["weight_kg"],
            "queried_at": result["queried_at"],
            "applied_filters": product["applied_filters"],
            "display_status": "실시간 가격",
        })
    report["queried_at"] = result["queried_at"]
    report["diagnostics"] = result["diagnostics"]
    return report


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

    from market_api import get_market_prices

    result = get_market_prices(YUKHOE_PRICE_SOURCES)
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
