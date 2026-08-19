import streamlit as st
from html import escape

from menu_data import (
    KAKAO_CHAT_URL,
    get_card_data,
    get_geumcheon_market_data,
    get_today_market_report,
)
from price_card import CATEGORY_REPORT_SIZE, create_market_report_png, create_price_card_png

# =================================================================
# 1. 페이지 설정 및 디자인 CSS
# =================================================================
st.set_page_config(page_title="축산 메뉴 연구소", layout="wide")

st.markdown("""
<style>
#MainMenu, footer, header {visibility: hidden;}
:root { color-scheme: light; }
.stApp, .stApp button, .stApp input, .stApp a {
    font-family: Pretendard, -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo",
                 "Noto Sans KR", "Malgun Gothic", sans-serif;
}
.stApp { background: #ffffff; color: #171a18; overflow-x: clip; }
.stApp *, .stApp *::before, .stApp *::after { box-sizing: border-box; }
.block-container {
    width: 100%; max-width: 760px; min-width: 0; margin-left: auto; margin-right: auto;
    padding-top: 1.1rem; padding-bottom: 5rem;
}
.hero-copy { margin-top: 108px; margin-bottom: 24px; text-align: center; }
.hero-title {
    margin: 0; color: #12291f; font-size: 26px !important; font-weight: 750 !important;
    line-height: 1.3 !important; letter-spacing: -0.025em;
}
.hero-description {
    margin: 14px 0 0; color: #606762; font-size: 16px; font-weight: 450;
    line-height: 1.65; letter-spacing: -0.01em;
}
.hero-mobile-break { display: none; }
.today-market { margin: 30px 0 16px; }
.today-market-heading { margin-bottom: 18px; text-align: center; }
.today-market-title { margin: 0; color: #12291f; font-size: 23px !important; font-weight: 780 !important; line-height: 1.35 !important; letter-spacing: -.025em; }
.today-market-caption { margin: 7px auto 0; max-width: 540px; color: #747c77; font-size: 14px !important; line-height: 1.6 !important; }
.hero-copy, .today-market-heading, .search-section-label,
.st-key-today_market_controls, [data-testid="stHorizontalBlock"],
[data-testid="column"], [data-testid="stTextInput"], [data-testid="stButton"] {
    min-width: 0;
}
.hero-title, .hero-description, .today-market-title, .today-market-caption {
    max-width: 100%; overflow-wrap: anywhere;
}
.st-key-today_market_controls [data-testid="stButton"] button { min-height: 48px; border-radius: 11px; font-size: 14px; font-weight: 700; }
.st-key-today_market_overall button { min-height: 58px !important; border-color: #173f30 !important; background: #173f30 !important; color: #ffffff !important; font-size: 16px !important; }
.st-key-today_market_toggle button { min-height: 52px !important; border-color: #b9c6bf !important; background: #ffffff !important; color: #173f30 !important; }
.st-key-today_market_controls [data-testid="stImage"] { margin-top: 18px; border: 1px solid #e3ded2; border-radius: 14px; overflow: hidden; }
.today-market-selection { margin: 18px 0 8px; color: #173f30; font-size: 15px; font-weight: 750; text-align: center; }
.search-section-label { margin: 2px 0 12px; color: #68716c; font-size: 13px; font-weight: 700; text-align: center; }
[data-testid="stTextInput"] { margin: 0; }
[data-testid="stTextInput"] input {
    min-height: 72px; padding: 0 26px; border: 1px solid #d9dedb;
    border-radius: 12px; background: #ffffff; color: #171a18; font-size: 18px;
    box-shadow: none;
}
[data-testid="stTextInput"] input::placeholder { color: #858c87; opacity: 1; }
[data-testid="stTextInput"] input:focus {
    border-color: #173f30; box-shadow: 0 0 0 1px #173f30;
}
[data-testid="stHorizontalBlock"] { align-items: stretch; }
[data-testid="stHorizontalBlock"] [data-testid="stButton"] button {
    min-height: 72px; border: 1px solid #173f30; border-radius: 12px;
    background: #173f30; color: #ffffff; font-size: 16px; font-weight: 700;
    box-shadow: none;
}
[data-testid="stHorizontalBlock"] [data-testid="stButton"] button:hover,
[data-testid="stHorizontalBlock"] [data-testid="stButton"] button:focus {
    border-color: #123326; background: #123326; color: #ffffff;
}
[data-testid="stAlert"], [data-testid="stExpander"] {
    border: 1px solid #e1e5e2; border-radius: 12px;
    box-shadow: none; overflow: hidden; background: #ffffff;
}
[data-testid="stAlert"] > div { color: #28302c; }
[data-testid="stExpander"] details summary { min-height: 50px; color: #173f30; font-weight: 650; }
[data-testid="stDownloadButton"] { margin-top: 12px; }
[data-testid="stDownloadButton"] button {
    min-height: 52px; border: 1px solid #173f30; border-radius: 12px;
    background: #ffffff; color: #173f30; font-size: 15px; font-weight: 700;
}
[data-testid="stDownloadButton"] button:hover,
[data-testid="stDownloadButton"] button:focus { border-color: #123326; background: #f6f7f4; color: #123326; }
.result-card { margin-top: 26px; border: 1px solid #e5e1d8; border-radius: 14px; background: #ffffff; overflow: hidden; }
.result-hero { padding: 27px 26px 24px; background: #f7f6f1; }
.result-eyebrow { color: #68716c; font-size: 14px; font-weight: 650; }
.result-eyebrow span { margin-left: 5px; color: #8b764a; }
.result-pick { margin-top: 7px; color: #9a7a3d; font-size: 30px; font-weight: 780; line-height: 1.25; letter-spacing: -.03em; }
.result-recommendation { margin-top: 5px; color: #12291f; font-size: 18px; font-weight: 700; line-height: 1.45; }
.result-body { padding: 18px 26px 24px; }
.result-priority { display: grid; grid-template-columns: 1.35fr 1fr; gap: 10px; }
.result-priority-item { min-height: 106px; padding: 17px 18px; border-radius: 11px; background: #f6f7f4; }
.result-priority-label { color: #56615b; font-size: 13px; font-weight: 700; line-height: 1.5; }
.result-priority-value { margin-top: 7px; color: #173f30; font-size: 17px; font-weight: 720; line-height: 1.5; }
.result-market-note { margin-top: 7px; color: #8b764a; font-size: 16px; font-weight: 720; line-height: 1.5; }
.result-market-list { margin: 8px 0 0; padding-left: 20px; color: #173f30; font-size: 15px; font-weight: 700; line-height: 1.7; }
.result-market-footnote { margin-top: 8px; color: #7a817d; font-size: 12px; font-weight: 500; line-height: 1.5; }
.result-supporting { margin-top: 18px; }
.result-support-row { display: grid; grid-template-columns: 100px 1fr; gap: 16px; padding: 10px 0; }
.result-support-row + .result-support-row { border-top: 1px solid #f0f1ee; }
.result-support-label { color: #7a817d; font-size: 13px; font-weight: 650; line-height: 1.6; }
.result-support-value { color: #535c57; font-size: 14px; font-weight: 500; line-height: 1.65; }
.result-stock { color: #747b77; font-weight: 650; }
.result-kakao { display: flex; align-items: center; justify-content: center; min-height: 52px; margin-top: 18px; border-radius: 12px; background: #d5ad55; color: #171a18 !important; font-size: 15px; font-weight: 700; text-decoration: none !important; }
.result-kakao:hover, .result-kakao:focus { background: #caa044; }
.market-container { margin-top: 16px; }
.market-cta {
    display: flex; align-items: center; justify-content: center; min-height: 50px;
    border: 1px solid #173f30; border-radius: 12px; color: #173f30 !important;
    font-size: 15px; font-weight: 680; text-decoration: none !important;
}
.btn-container { display: flex; justify-content: center; margin: 16px 0 0; }
.btn-kakao {
    display: flex; align-items: center; justify-content: center; min-height: 50px; padding: 0 20px;
    border-radius: 12px; font-weight: 680; text-decoration: none !important; text-align: center;
    width: 100%; background: #d5ad55; color: #171a18 !important; font-size: 15px; box-shadow: none;
}
@media (max-width: 700px) {
    html, body, .stApp { max-width: 100%; overflow-x: hidden; }
    .block-container {
        width: 100% !important; max-width: 100% !important; min-width: 0 !important;
        margin: 0 auto !important; padding: 0.35rem 16px 1.5rem !important;
    }
    .hero-copy { margin-top: 42px; margin-bottom: 20px; }
    .hero-title { font-size: 27px !important; line-height: 1.35 !important; word-break: keep-all; }
    .hero-mobile-break { display: block; }
    .hero-description { margin-top: 12px; font-size: 15px !important; line-height: 1.6 !important; word-break: keep-all; }
    .today-market { margin: 26px 0 14px; }
    .today-market-heading { margin-bottom: 15px; }
    .today-market-title { font-size: 22px !important; line-height: 1.4 !important; word-break: keep-all; }
    .today-market-caption { font-size: 13px !important; line-height: 1.6 !important; word-break: keep-all; }
    .search-section-label { margin-top: 4px; }
    [data-testid="stHorizontalBlock"] { width: 100% !important; flex-direction: column; gap: 10px; }
    [data-testid="column"] { width: 100% !important; min-width: 0 !important; flex: 1 1 100% !important; }
    .st-key-today_market_controls [data-testid="stHorizontalBlock"] { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }
    .st-key-today_market_controls [data-testid="column"] { width: auto !important; min-width: 0 !important; }
    .st-key-today_market_controls [data-testid="stButton"] button { min-height: 48px; padding-left: 8px; padding-right: 8px; font-size: 13px; }
    [data-testid="stTextInput"], [data-testid="stTextInput"] > div,
    [data-testid="stTextInput"] input, [data-testid="stButton"],
    [data-testid="stButton"] button { width: 100% !important; max-width: 100% !important; }
    [data-testid="stTextInput"] input { min-height: 64px; padding: 0 20px; font-size: 17px; }
    [data-testid="stHorizontalBlock"] [data-testid="stButton"] button { min-height: 52px; }
    .result-card { margin-top: 22px; }
    .result-hero { padding: 23px 20px 21px; }
    .result-pick { font-size: 27px; }
    .result-recommendation { font-size: 17px; }
    .result-body { padding: 16px 20px 21px; }
    .result-priority { grid-template-columns: 1fr; gap: 8px; }
    .result-priority-item { min-height: auto; padding: 15px 16px; }
    .result-priority-label { font-size: 14px; }
    .result-priority-value, .result-market-note { margin-top: 5px; font-size: 16px; }
    .result-supporting { margin-top: 13px; }
    .result-support-row { grid-template-columns: 82px 1fr; gap: 12px; padding: 9px 0; }
    .result-support-label { font-size: 14px; }
    .result-support-value { font-size: 15px; line-height: 1.6; }
    .result-kakao { min-height: 54px; margin-top: 15px; font-size: 16px; }
}
</style>
""", unsafe_allow_html=True)

# =================================================================
# 4. 40개 전 품목 데이터베이스
# =================================================================
expert_db = {
"육회": {
    "summary": "육회는 주로 우둔살, 꾸리살, 홍두깨살, 설도 부위를 사용합니다.",
    "pro_pick": "우둔살",
    "pro_reason": "우둔살은 근육의 결이 일정하고 마블링(지방)이 적어 담백하며, 육회 고유의 진한 육향과 부드러운 탄력을 직관적으로 전달하는 표준 부위입니다.",
    "other_parts": {"꾸리살": "앞다리 위쪽 부위로 운동량이 많아 육질이 쫀득하고 감칠맛이 좋습니다.", "홍두깨살": "결이 곧아서 균일한 규격으로 세절하기 용이하며 기름기가 거의 없습니다.", "설도/설깃": "고기 색이 밝고 연하여 가성비 믹싱용으로 훌륭합니다."},
    "pro_tip": "생으로 먹는 육회는 마블링이 많으면 느끼합니다. 1등급 전후가 가장 찰지고 맛이 좋으며 등급보다는 도축 일자의 신선도가 핵심입니다."
},
"쌀국수": {
    "summary": "쌀국수는 주로 양지, 차돌박이, 사태 부위를 주로 사용합니다.",
    "pro_pick": "양지(차돌양지)",
    "pro_reason": "육수를 우려낼 때 깊고 진한 육향을 내뿜으며, 삶아낸 후 고명으로 올렸을 때 질겨지지 않고 부드습니다.",
    "other_parts": {"차돌박이": "고소한 우지방 풍미가 국물 전체에 녹아들어 묵직한 맛을 완성합니다.", "사태": "지방이 적고 콜라겐이 발달해 푹 삶았을 때 쫀득한 식감이 일품입니다."},
    "pro_tip": "토핑 시 1~2mm 내외로 얇고 균일하게 썰어내야 뜨거운 육수 안에서 고기가 질겨지지 않고 면과 겉돌지 않습니다."
},
"갈비탕": {
    "summary": "갈비탕은 찜갈비(백립), 탕갈비, 마구리 부위를 주로 사용합니다.",
    "pro_pick": "본갈비(탕갈비)",
    "pro_reason": "살밥이 두텁게 붙어 있어 그릇에 담아냈을 때 압도적인 비주얼을 자랑하며 씹었을 때 육즙이 가득합니다.",
    "other_parts": {"마구리": "갈비뼈 양끝 부위로, 고기는 적지만 깊고 구수한 국물용 육수를 내는 데 필수적입니다.", "찜갈비": "수입산 정형 규격이 좋아 대형 업소에서 원가 절감형 고명으로 혼용합니다."},
    "pro_tip": "탕갈비와 마구리를 7:3 비율로 혼합 사용하는 것이 국물 퀄리티와 푸짐한 비주얼을 동시에 챙기는 외식업계 공식입니다."
},
"삼겹살": {
    "summary": "삼겹살은 일반 삼겹살과 미박삼겹(오겹살) 부위를 주로 사용합니다.",
    "pro_pick": "미박삼겹(오겹살)",
    "pro_reason": "껍데기가 붙어 있어 구웠을 때 껍데기의 쫀득함, 지방의 고소함, 살코기의 육즙 3박자가 극대화됩니다.",
    "other_parts": {"일반삼겹": "껍데기를 걷어내 정형이 깔끔하고 불판 위에서 타거나 튀는 현상이 적어 관리가 편합니다.", "대패삼겹": "하등급 삼겹이나 전지를 얇게 슬라이스하여 높은 가성비와 빠른 회전율을 타깃으로 합니다."},
    "pro_tip": "구이용 원육은 살코기와 지방층이 4:6 비율로 교차된 것이 가장 맛있습니다. 냉동 삼겹살은 3~4mm 두께가 육즙 손실을 막는 황금 두께입니다."
},
"제육볶음": {
    "summary": "제육볶음은 주로 돼지 앞다리살(전지)과 뒷다리살(후지)을 사용합니다.",
    "pro_pick": "앞다리살(전지)",
    "pro_reason": "근육 사이에 적당한 지방층이 분포되어 있어 고온의 불길에 볶아내도 질겨지거나 퍽퍽해지지 않고 부드럽습니다.",
    "other_parts": {"뒷다리살(후지)": "지방이 거의 없어 가성비 극대화를 노리는 단체 급식소에서 주로 선택합니다.", "대패삼겹살": "기름지고 고소한 맛을 극대화한 프리미엄 기사식당풍 제육볶음에 믹싱됩니다."},
    "pro_tip": "볶음용 전지는 2mm 두께 슬라이스가 양념이 안쪽까지 가장 잘 배어드는 규격입니다."
},
"돈가스": {
    "summary": "돈가스는 돼지 등심과 안심 부위를 주로 사용합니다.",
    "pro_pick": "등심",
    "pro_reason": "적당한 육질의 단단함이 있어 튀김옷과의 밀착력이 우수하며, 튀겼을 때 씹는 맛이 직관적이고 고소합니다.",
    "other_parts": {"안심": "결이 고밀도로 부드러워 결을 살려 동그랗게 튀겨내는 프리미엄 카츠 메뉴에 쓰입니다.", "후지(뒷다리)": "민찌(분쇄육) 형태로 정형하여 가성비 멘치카츠나 피카츄돈가스류에 쓰입니다."},
    "pro_tip": "두툼한 일식 카츠의 경우, 미세 정교한 연육기(핀팅) 작업을 거치지 않으면 수축 현상이 일어나 튀김옷이 분리되므로 사전 연육육을 공급받는 게 마진에 이롭습니다."
},
"감자탕": {
    "summary": "감자탕은 돼지 목뼈와 등뼈 부위를 주로 사용합니다.",
    "pro_pick": "목뼈",
    "pro_reason": "등뼈에 비해 골분 내부 수분이 많고 살코기 자체가 부드러워 푹 끓였을 때 살이 뼈에서 부드럽게 발라집니다.",
    "other_parts": {"등뼈": "가격이 목뼈보다 저렴하여 양을 푸짐하게 산처럼 쌓아주는 가성비 전략 업소에서 선호합니다."},
    "pro_tip": "수입산(유럽/캐나다산 등) 뼈가 국내산보다 정형 시 살밥을 훨씬 많이 남겨두기 때문에 외식 업소 수율 면에서 훨씬 유리합니다."
},
"닭볶음탕": {
    "summary": "닭볶음탕은 육계 9호, 10호, 11호 전육을 주로 사용합니다.",
    "pro_pick": "육계 10호",
    "pro_reason": "닭고기 육질의 탄력이 가장 알맞게 차오른 시기로, 토막 조리 시 양념이 잘 침투하며 살밥의 양이 가장 푸짐해 보입니다.",
    "other_parts": {"9호 이하": "살이 연하나 토막 시 크기가 작아 탕 안에서 고기가 쉽게 바스러집니다.", "12호 이상": "살밥은 많으나 육질이 다소 질겨져 장시간 압력 조리가 요구됩니다."},
    "pro_tip": "부위별 조리 속도를 맞추기 위해 가슴살 부위에는 미세하게 칼집을 넣어 양념 베임 속도를 다리살과 맞춰주어야 합니다."
},
"삼계탕": {
    "summary": "삼계탕은 주로 삼계 전용 닭인 웅추 또는 백세미 5호, 6호를 사용합니다.",
    "pro_pick": "웅추(생후 50일 미만 수탉)",
    "pro_reason": "살이 퍼지지 않고 쫄깃하며 오랜 시간 끓여내도 닭 가슴살까지 퍽퍽함 없이 찰진 식감을 완벽히 유지합니다.",
    "other_parts": {"백세미": "일반 육계와 산란계의 교배종으로 성장이 빨라 단가가 저렴하고 살집이 부드럽습니다."},
    "pro_tip": "삼계탕용 원육은 뚝배기 규격에 맞는 5~6호 선별이 절대적입니다. 껍질이 조리 중 벗겨지면 비주얼이 손상되므로 피막 탄력이 살아있는 원육을 써야 합니다."
},
"곰탕": {
    "summary": "곰탕은 소 사골, 잡뼈, 반골꼬리와 사태, 양지 부위를 사용합니다.",
    "pro_pick": "한우 사골 + 모둠잡뼈",
    "pro_reason": "사골만 끓이면 국물이 맑고 담백하지만, 잡뼈를 4:6 비율로 혼합 시 젤라틴과 콜라겐이 다량 용출되어 묵직하고 고소한 유백색 국물이 완성됩니다.",
    "other_parts": {"양지/사태": "고기곰탕용 고명으로 필수적이며 국물에 고기 자체의 단맛과 진한 육향을 더해줍니다."},
    "pro_tip": "사골 핏물은 최소 6시간 이상 흐르는 물에 빼야 잡내가 안 생깁니다. 첫 번째 끓여 낸 물은 버리고 두 번째, 세 번째 국물을 블렌딩하는 것이 황금 레시피입니다."
},
"육개장": {
    "summary": "육개장은 소 사태, 양지, 홍두깨살을 주로 사용합니다.",
    "pro_pick": "양지머리",
    "pro_reason": "근막과 부드러운 지방이 결마다 박혀 있어 푹 삶았을 때 구수한 기름 풍미가 매콤한 육수와 환상적으로 어우러집니다.",
    "other_parts": {"사태": "결이 굵고 단단해 얇게 슬라이스 컷하여 정갈한 비주얼을 내는 고명으로 쓸 때 유리합니다.", "홍두깨살": "기름기 없이 담백하게 손으로 찢어 올리는 전통 시장식 육개장에 적합합니다."},
    "pro_tip": "주방 인건비를 줄이려면 기계 슬라이스용 사태 원육을 1.5mm로 얇게 밀어 끓이는 방식이 회전율에 이롭습니다."
},
"꼬리곰탕": {
    "summary": "꼬리곰탕은 소 알꼬리와 꼬리반골 부위를 주로 사용합니다.",
    "pro_pick": "알꼬리",
    "pro_reason": "뼈 주변을 감싸고 있는 단단한 근육과 지방의 밸런스가 완벽해 뜯어먹는 살밥의 재미와 쫀득한 식감이 독보적입니다.",
    "other_parts": {"꼬리반골": "꼬리뼈 시작점 부위로, 알꼬리에 비해 뼈의 부피가 크고 살밥은 적으나 국물을 진하게 우려내는 단가 방어용 쓰입니다."},
    "pro_tip": "수입산 호주/미국산 알꼬리가 살밥이 두터워 외식업 선호도가 매우 높습니다."
},
"도가니탕": {
    "summary": "도가니탕은 소 무릎뼈(도가니)와 스지(힘줄) 부위를 주로 사용합니다.",
    "pro_pick": "소 도가니",
    "pro_reason": "소 한 마리에서 극소량만 나오는 희귀 부위로 특유의 부드럽게 감기는 고급 젤라틴 식감이 보양식 가치를 증명합니다.",
    "other_parts": {"스지(알스지)": "아킬레스건 부위로 도가니와 식감이 흡사하면서 단가는 훨씬 저렴해, 실제 도가니와 스지를 3:7 비율로 혼용하는 것이 대중적 원가 공식입니다."},
    "pro_tip": "도가니와 스지는 과도하게 삶으면 국물에 다 녹아버리므로 꼬들함이 약간 남아있을 때 건져내어 급냉 후 슬라이스해야 수율을 지킵니다."
},
"소머리국밥": {
    "summary": "소머리국밥은 소머리 전육(볼살, 콧살, 우설, 귀밑살 등)을 사용합니다.",
    "pro_pick": "뽈살(볼더기살)",
    "pro_reason": "소머리 부위 중 운동량이 가장 많아 지방이 거의 없고 쫄깃하면서도 사태보다 연해 손님들이 가장 선호합니다.",
    "other_parts": {"우설": "식감이 매우 부드럽고 특수 부위로서 가치가 높아 따로 수육 메뉴로 빼서 판매 시 높은 마진을 확보할 수 있습니다.", "콧살/가죽살": "콜라겐 덩어리로 쫀득한 식감의 재미를 유발합니다."},
    "pro_tip": "소머리는 손질이 까다롭고 잡내 제거 실패율이 높으므로, 뼈를 완전히 제거하고 1차 자숙(삶기) 가공이 끝난 원육 가공품을 받는 것이 팩트입니다."
},
"소불고기": {
    "summary": "소불고기는 주로 소 목심, 전도, 설도, 우둔 부위를 슬라이스하여 사용합니다.",
    "pro_pick": "목심(척아이롤)",
    "pro_reason": "살코기 속에 가느다란 마블링이 박혀 있어 양념에 재워두었을 때 연육 성분이 잘 스며들고 조리 후에도 부드럽습니다.",
    "other_parts": {"설도/우둔": "기름기가 없는 완벽한 살코기 부위로 가성비 무한리필 불고기나 뚝배기 불고기 업소에서 얇게 밀어 대량 조리용으로 사용합니다."},
    "pro_tip": "소불고기용 원육 두께는 1.8mm~2mm 슬라이스가 골든 스탠다드입니다. 이보다 두꺼우면 질기고 고기가 뭉칩니다."
},
"차돌박이": {
    "summary": "차돌박이는 소 양지 하단부의 백색 단단한 지방층 부위를 사용합니다.",
    "pro_pick": "차돌박이 오리지널",
    "pro_reason": "단단한 차돌지방은 일반 떡지방과 달리 구웠을 때 녹아 사라지지 않고 서각거리는 특유의 고소한 식감을 내뿜습니다.",
    "other_parts": {"우삼겹(업진살)": "차돌박이와 모양은 유사하나 지방이 훨씬 부드럽고 연해 저가형 고깃집에서 대체 육으로 다량 소비됩니다."},
    "pro_tip": "기름 함량이 높은 특수 부위이므로 1.5mm 이하 초박형 슬라이스 정형 기술이 필수입니다. 조금만 두꺼워도 고무줄처럼 질겨집니다."
},
"육사시미": {
    "summary": "육사시미는 우둔살, 꾸리살, 치마살을 주로 사용합니다.",
    "pro_pick": "한우 우둔살",
    "pro_reason": "기름기가 섞이지 않은 순수 단백질 섬유질 구조로 이루어져 있어, 생으로 먹었을 때 찰진 식감과 씹을수록 단맛이 도는 육즙이 단연 압권입니다.",
    "other_parts": {"치마살": "결 사이에 고운 마블링이 있어 완전히 부드러운 살살 녹는 식감의 고급 특수 육사시미 라인업에 쓰입니다."},
    "pro_tip": "육사시미는 도축 후 24시간 이내의 사후강직이 풀리기 전 고기를 공수해야 접시를 뒤집어도 떨어지지 않는 오리지널 찰기를 확보합니다."
},
"뭉티기": {
    "summary": "뭉티기는 당일 도축된 한우 우둔살 내부 처진개살, 꾸리살 부위를 사용합니다.",
    "pro_pick": "한우 처진개살",
    "pro_reason": "지방과 근막을 100% 수작업으로 걷어낸 순수 붉은 살코기로 도축 직후 수분 보유력이 정점에 달해 쫀득함이 예술입니다.",
    "other_parts": {"일반 우둔": "뭉티기 물량 부족 시 대체하여 근막 제거 후 칼로 뭉텅뭉텅 썰어 공급합니다."},
    "pro_tip": "뭉티기는 절대 냉장 숙성을 거치면 안 됩니다. 숙성이 시작되면 수분이 빠져나와 찰기가 죽으므로 오직 당일 도축 공수가 생명입니다."
},
"곱창": {
    "summary": "곱창은 소의 소장 부위를 가공하여 사용합니다.",
    "pro_pick": "한우 알곱창",
    "pro_reason": "수입산에 비해 장 내부의 '곱'이 꽉 차 있고 벽면이 얇아 구웠을 때 크림처럼 고소한 풍미와 부드러움의 조화가 최상급입니다.",
    "other_parts": {"수입 가공 곱창": "곱을 인위적으로 충전하거나 연육 처리하여 가성비 곱창 전골이나 배달 전문점에 다량 유통됩니다."},
    "pro_tip": "세척 시 내부 곱이 씻겨나가지 않게 끝을 묶는 전처리가 생명이며, 수율이 60% 이상 유지되는 스팀 자숙 가공 원육이 주방 로스를 막아줍니다."
},
"대창": {
    "summary": "대창은 소의 대장 부위를 뒤집어 정형해 사용합니다.",
    "pro_pick": "소 대창 (원형 정형)",
    "pro_reason": "대장의 바깥쪽 지방층을 안쪽으로 쏙 뒤집어 정형한 부위로, 구울 때 지방을 가두어 기름 겉바속촉의 극치를 보여줍니다.",
    "other_parts": {"홍창/막창": "대창과 이어지는 부위로 겉면이 두껍고 씹는 맛이 강해 모둠 구이의 구색용으로 레이어드됩니다."},
    "pro_tip": "연육제 배합 세척이 끝난 백색 정형 대창을 공급받아야 주방 세척 지옥에서 해방됩니다."
},
"막창": {
    "summary": "막창은 소의 네 번째 위(홍창) 또는 돼지의 직장 부위를 사용합니다.",
    "pro_pick": "소 막창(홍창)",
    "pro_reason": "소 한 마리에서 소량만 나오는 특수 부위로, 콜라겐 섬유가 촘촘히 얽혀 있어 씹을수록 고소하고 서각거리는 질감을 선사합니다.",
    "other_parts": {"돼지 막창": "동글동글하게 썰어 바짝 구워 먹는 안주 메뉴로, 누린내를 잡는 세척 공정이 퀄리티를 좌우합니다."},
    "pro_tip": "조리 전 스팀 자숙 공정을 거친 막창을 쓰면 구이 시간을 3배 이상 단축해 테이블 회전율을 극대화할 수 있습니다."
},
"스지탕": {
    "summary": "스지탕은 소의 아킬레스건 및 사태 주변 힘줄 부위를 사용합니다.",
    "pro_pick": "알스지(오리지널 아킬레스건)",
    "pro_reason": "단단하고 밀도가 높아 오랜 시간 고아내도 형태가 무너지지 않으며 진득하게 입술이 붙는 듯한 오리지널 젤라틴 육수를 뿜어냅니다.",
    "other_parts": {"잡스지/소스지": "사태 정형 시 나오는 얇은 근막 힘줄 부위로, 가격이 저렴하여 탕 내부 양을 많아 보이게 하는 용도로 훌륭합니다."},
    "pro_tip": "90도 온도로 2시간 30분 자숙 후 냉각 세절하는 타이밍 공정을 표준화해야 수율을 지킵니다."
},
"소고기수육": {
    "summary": "소고기수육은 주로 아롱사태, 양지삼합, 볼살 부위를 사용합니다.",
    "pro_pick": "아롱사태",
    "pro_reason": "단면을 자랐을 때 결마다 투명한 전분질 힘줄이 박혀 있어 삶아내면 시각적 완성도가 높고 쫄깃함과 부드러움이 공존합니다.",
    "other_parts": {"차돌양지": "기름지고 고소한 한우 전통 평양냉면식 제육/수육 라인에 배치됩니다.", "머리고기": "쫀득한 식감 위주의 가성비 실비집 스타일 수육용입니다."},
    "pro_tip": "수육은 식으면 급격히 육질이 굳으므로 자작한 육수와 함께 워머 불판에 올려 계속 데워가며 드시게 해야 합니다."
},
"스키야키": {
    "summary": "스키야키는 주로 소 전지, 등심, 목심 부위를 아주 얇게 슬라이스하여 사용합니다.",
    "pro_pick": "수입산 목심(척아이롤)",
    "pro_reason": "적절한 등심 근육과 목심 지방 비율을 가지고 있어 간장 소스가 잘 코팅되며, 살짝 익혀 계란 노른자에 찍어 먹었을 때 가장 부드럽습니다.",
    "other_parts": {"우삼겹": "기름진 고소함을 선호하는 캐주얼 가성비 샤브/스키야키 뷔페 업소에서 다량 채택합니다."},
    "pro_tip": "두께가 1.5mm로 고도로 얇아야 타레 소스가 끓는 짧은 순간에 야채와 속도를 맞추어 익습니다."
},
"소고기뭇국": {
    "summary": "소고기뭇국은 소 양지, 사태, 국거릿용 잡육 부위를 사용합니다.",
    "pro_pick": "양지(양지머리)",
    "pro_reason": "지방에서 우러나오는 고소한 감칠맛과 국거리 부위 중 가장 진한 담백한 육향이 무의 시원한 성분과 만나 깊은 국물을 완성합니다.",
    "other_parts": {"사태": "지방기 없이 깔끔하고 맑은 국물을 타깃으로 하는 뭇국에 적합합니다.", "정육잡육": "설도, 앞다리 등 정형 후 남은 부위로 가성비 백반집 국물용입니다."},
    "pro_tip": "참기름에 고기 겉면이 회색빛이 돌 때까지 충분히 볶다가 물을 붓고 끓여야 고기 육즙이 내부에 갇힙니다."
},
"오겹살": {
    "summary": "오겹살은 껍데기가 붙어 있는 돼지 삼겹살(미박삼겹) 부위입니다.",
    "pro_pick": "미박삼겹(오겹 원육)",
    "pro_reason": "지방 구조 위에 미세 콜라겐 껍데기 층이 한 층 더 얹어져 고기를 겉은 바삭하고 속은 촉촉하게 구워내는 최상의 레이어드를 제공합니다.",
    "other_parts": {"일반 삼겹": "껍데기를 기계 정형으로 완전히 박피하여 균일하고 부드러운 고기 맛 중심의 스탠다드 삼겹살용입니다."},
    "pro_tip": "불판 온도를 220도 이상 올린 상태에서 지방과 껍데기 면을 먼저 지져야 질기지 않고 크리스피한 식감이 삽니다."
},
"목살": {
    "summary": "목살은 돼지의 목 부위 근육 계열 단면을 정형하여 사용합니다.",
    "pro_pick": "알목심(중심부)",
    "pro_reason": "눈꽃 마블링이 아름답게 박혀 있는 중심 알짜배기 부위로, 두툼하게 썰어 숯불에 구웠을 때 스테이크를 능가하는 육즙을 머금게 됩니다.",
    "other_parts": {"일반목살": "지방이 적고 살코기 비중이 높아 가성비 찌개용, 카레용 정육 또는 캠핑용 바비큐 고기로 무난합니다."},
    "pro_tip": "목살은 삼겹살보다 지방이 적기 때문에 최소 2cm~3cm 두께로 두툼하게 커팅해야 마르는 것을 막습니다."
},
"항정살": {
    "summary": "항정살은 돼지 목덜미에서 어깨 부위까지 이어지는 천겹살 특수부위입니다.",
    "pro_pick": "통항정살(정형 완료)",
    "pro_reason": "살코기 사이에 미세한 마블링이 천 개나 박혀 있어, 구웠을 때 타 부위와 비교 불가능한 아삭아삭 씹히는 특유의 식감과 고소함이 가득합니다.",
    "other_parts": {"칼항정(슬라이스)": "결 반대로 정교하게 슬라이스 되어 나와 로스율이 없고 서빙 속도가 매우 빠릅니다."},
    "pro_tip": "항정살은 겉지방이 80% 이상 완벽히 제거된 정형 완료 규격 원육을 받아 쓰는 게 매장 마진 방어에 현명합니다."
},
"가브리살": {
    "summary": "가브리살은 돼지 등심 앞부분 상단에 붙어있는 등심덧살입니다.",
    "pro_pick": "수제 정형 가브리살",
    "pro_reason": "소고기 같은 짙은 선홍색 육색을 띠며, 삼겹살보다 연하고 부드러우면서 토시살 같은 진한 육향을 지니고 있습니다.",
    "other_parts": {"일반 등심덧살": "돈가스용 등심 분리 시 얇게 떨어져 주로 찌개용 특수 정육으로 저렴하게 소비되기도 합니다."},
    "pro_tip": "80% 정도만 익혀 미디엄-웰던 상태로 먹을 때 가장 부드럽고 육즙이 흐릅니다."
},
"갈매기살": {
    "summary": "갈매기살은 돼지의 횡격막(가로막살) 부위 특수 부위입니다.",
    "pro_pick": "통갈매기살",
    "pro_reason": "소고기의 안창살에 해당하는 부위로 힘 있는 근섬유 구조 덕분에 쫄깃함과 진한 육향이 일품입니다.",
    "other_parts": {"양념 갈매기살": "갈매기살 특유의 강한 피향을 제어하기 위해 마늘, 간장 베이스로 즉석 주물럭 양념한 규격입니다."},
    "pro_tip": "미세한 벌집 칼집 정형 처리가 완료된 원육을 사용해야 손님이 질겨서 뱉어내는 사고를 막습니다."
},
"돼지갈비": {
    "summary": "돼지갈비는 정통 갈비뼈 부위와 목살/전지 양념 가공육을 주로 사용합니다.",
    "pro_pick": "한돈 정통 갈비 + 목살 혼합",
    "pro_reason": "뼈에 붙은 갈비살의 뜯는 맛과 목살의 균일한 살코기 배합률이 5:5로 조화를 이룰 때 만족도와 원가 방어가 동시에 가능합니다.",
    "other_parts": {"포갈비": "오직 갈비뼈 원육만을 일일이 칼로 포를 뜬 프리미엄 갈비로 높은 단가의 고급 매장에 적합합니다."},
    "pro_tip": "간장 양념 배합 시 배, 양파 등 천연 과일 연육을 넣고 48시간 저온 숙성 기간을 거쳐야 숯불 위에서 고기가 타지 않습니다."
},
"두루치기": {
    "summary": "두루치기는 돼지 앞다리살, 뒷다리살, 삼겹 정육을 사용합니다.",
    "pro_pick": "앞다리살(전지) 3mm 두께",
    "pro_reason": "채소와 함께 졸여가며 먹는 메뉴 특성상, 전지의 미세 지방과 콜라겐이 국물에 녹아들어 소스를 묵직하게 잡아줍니다.",
    "other_parts": {"삼겹살/오겹살": "단가가 높은 프리미엄 짜글이식 두루치기 전문점에서 중독성 있는 풍미를 위해 일부 혼용합니다."},
    "pro_tip": "고기가 너무 얇으면 형체가 사라지므로 제육용보다 약간 두꺼운 3mm 규격 세절 원육 사용이 팩트입니다."
},
"김치찜": {
    "summary": "김치찜은 돼지 앞다리살, 사태, 통삼겹살 부위를 주로 사용합니다.",
    "pro_pick": "돼지 사태(통사태)",
    "pro_reason": "장시간 푹 쪄내는 조리법 특성상 사태의 힘줄 콜라겐이 젤라틴화되어 숟가락으로 찢어질 만큼 결이 부드러워지면서도 형태를 유지합니다.",
    "other_parts": {"통삼겹살": "비주얼적 가치가 높아 묵은지에 길게 싸서 먹는 시그니처 메뉴에 시각적 고명으로 투입됩니다."},
    "pro_tip": "1차로 된장과 함께 통으로 겉면만 가볍게 삶아 불순물을 빼낸 후 본 조리에 들어가야 깔끔합니다."
},
"갈비찜": {
    "summary": "갈비찜은 소 갈비 또는 돼지 갈비 부위를 사용합니다.",
    "pro_pick": "소 본갈비",
    "pro_reason": "마블링이 적당히 형성된 소 중심 갈비 부위로 양념 고온 조리 시 고기가 수축되거나 뼈에서 탈탈 떨어지는 현상이 적고 부드럽습니다.",
    "other_parts": {"돼지갈비": "명절 및 대중적 한식 밥집 가성비 매운 갈비찜 메뉴에 쓰이며 배달 팩으로 활성화되어 있습니다."},
    "pro_tip": "골분(뼈가루) 세척이 제대로 안 되면 이물감을 느끼므로, 원육 커팅 단면이 깨끗하게 정형 가공된 원육 라인 확보가 절대적입니다."
},
"김치찌개": {
    "summary": "김치찌개는 돼지 앞다리살(전지), 찌개용 후지, 삼겹 정육을 사용합니다.",
    "pro_pick": "돼지 앞다리살",
    "pro_reason": "지방과 살코기 비율이 3:7로 찌개 국물에 적당한 동물성 기름 풍미를 제공하면서 가성비가 매우 뛰어납니다.",
    "other_parts": {"돼지 후지": "원가는 낮으나 조리 후 고기가 마르고 퍽퍽해져 단독 사용은 비추천합니다."},
    "pro_tip": "전지 80%에 고소한 삼겹 지방 미세 정육 20%를 믹싱하여 기름막을 살짝 형성해 주는 것이 국물 맛을 올리는 팁입니다."
},
"돼지국밥": {
    "summary": "돼지국밥은 돼지 머리고기, 앞다리살, 삼겹살 부위를 사용합니다.",
    "pro_pick": "돼지 머리고기(자숙 머리정육)",
    "pro_reason": "귀밑살, 항정살 계열, 볼살 등 다양한 부위가 섞여 있어 한 그릇 안에서 부드러움과 쫄깃함을 동시에 느끼게 합니다.",
    "other_parts": {"앞다리살/삼겹살": "살코기 위주의 정갈하고 깔끔한 수육국밥 형태의 프랜차이즈에서 주로 고집합니다."},
    "pro_tip": "100% 뼈 제거 후 완벽 세척 자숙된 머리 정육 슬라이스 원육을 받아 조리 시간과 가스비를 절감하는 것이 현명합니다."
},
"탕수육": {
    "summary": "탕수육은 돼지 등심과 안심, 후지 부위를 주로 사용합니다.",
    "pro_pick": "돼지 등심",
    "pro_reason": "수분 함량이 적당해 튀김옷과의 밀착력이 가장 높고, 튀겨냈을 때 고기 식감이 정갈하게 씹히는 중식 표준 원육입니다.",
    "other_parts": {"안심": "극도로 부드러운 목화솜 탕수육 전문점에서 사용하나 단가가 높습니다.", "후지(뒷다리)": "원가가 매우 저렴해 저가형 세트 메뉴 중식당이나 분식집 탕수육용입니다."},
    "pro_tip": "손가락 굵기의 일정한 스틱 정형이 필수적입니다. 규격이 일정한 공장형 정형 등심 원육이 주방 마진 향상에 직결됩니다."
},
"수육": {
    "summary": "수육은 돼지 삼겹살, 오겹살, 앞다리살(전지) 부위를 주로 사용합니다.",
    "pro_pick": "통삼겹살",
    "pro_reason": "살코기와 마블링 지방이 층층이 균일하여 삶아냈을 때 비주얼이 정갈하고 육즙이 마르지 않아 호불호가 없습니다.",
    "other_parts": {"앞다리살(통전지)": "단가가 삼겹살의 절반 수준으로 가성비 수육 정식이나 국수 전문점 고명용으로 필수적입니다."},
    "pro_tip": "물이 완전히 끓을 때 고기를 넣어야 표면 단백질이 응고되면서 맛있는 육즙이 내부에서 빠져나가지 않습니다."
},
"보쌈": {
    "summary": "보쌈은 돼지 삼겹살과 앞다리살 부위를 주로 사용합니다.",
    "pro_pick": "수입 프리미엄 통삼겹살",
    "pro_reason": "유럽산 프리미엄 삼겹살은 국내산에 비해 과도한 떡지방 비중이 적고 오돌뼈가 깔끔히 제거되어 수율이 매우 좋습니다.",
    "other_parts": {"한돈 삼겹살": "국내산 브랜드 가치를 전면에 내세우는 프리미엄 전통 보쌈 전문점의 선택입니다.", "가성비 전지": "보쌈 배달 전문점에서 마진율을 올리기 위한 믹싱용으로 사용됩니다."},
    "pro_tip": "건져낸 후 한 김 식히거나 래핑하여 미세 뜸 들이기 숙성을 15분간 거친 후 썰어야 단면이 쫀쫀하게 정형됩니다."
},
"등갈비": {
    "summary": "등갈비는 돼지 등심 쪽에 붙어있는 갈비뼈와 살코기 부위(로인립)를 사용합니다.",
    "pro_pick": "수입산 프리미엄 로인립",
    "pro_reason": "국내산에 비해 뼈 위에 두툼한 살밥을 통째로 남겨두어 찜이나 구이 조리 시 고객이 먹을 고기 양이 월등히 많습니다.",
    "other_parts": {"스페인 이베리코 등갈비": "특유의 고소한 마블링 지방이 뼈 주변에 감겨있어 프리미엄 캠핑 바비큐용으로 좋습니다."},
    "pro_tip": "조리 전 반드시 등갈비 뒷면 안쪽 투명 근막을 칼끝으로 집어 당겨 벗겨내는 전처리 공정을 거쳐야 질겨지지 않습니다."
}
}

# 2. 검색 및 출력 제어 로직
if "today_market_selection" not in st.session_state:
    st.session_state.today_market_selection = None


def select_today_market(report_id):
    st.session_state.today_market_selection = report_id


def close_today_market():
    st.session_state.today_market_selection = None


with st.container(key="today_market_controls"):
    st.markdown(
        """
        <section class="today-market" aria-labelledby="today-market-title">
            <div class="today-market-heading">
                <h2 id="today-market-title" class="today-market-title">오늘의 축산물 실시간 단가</h2>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )
    st.button(
        "오늘의 종합 단가표 보기",
        key="today_market_overall",
        use_container_width=True,
        type="primary",
        on_click=select_today_market,
        args=("all",),
    )
    selected_report_id = st.session_state.today_market_selection
    if selected_report_id:
        selected_report = get_today_market_report(
            None if selected_report_id == "all" else selected_report_id,
            include_live_prices=True,
        )
        is_overall_report = selected_report_id == "all"
        report_size = None if is_overall_report else CATEGORY_REPORT_SIZE
        report_png = (
            create_market_report_png(
                selected_report["title"], selected_report["groups"],
                kakao_chat_url=KAKAO_CHAT_URL,
            )
            if report_size is None
            else create_market_report_png(
                selected_report["title"], selected_report["groups"],
                canvas_size=report_size, kakao_chat_url=KAKAO_CHAT_URL,
            )
        )
        st.markdown(
            f'<div class="today-market-selection">{escape(selected_report["title"])}</div>',
            unsafe_allow_html=True,
        )
        st.image(report_png, use_container_width=True)
        safe_name = (
            "오늘의_축산물" if is_overall_report
            else selected_report["groups"][0]["category_name"].replace(" ", "_")
        )
        download_label = (
            "종합 단가표 저장(PNG)" if is_overall_report
            else f'{selected_report["groups"][0]["category_name"]} 단가표 저장(PNG)'
        )
        st.download_button(
            download_label,
            data=report_png,
            file_name=f"동원_금천미트_{safe_name}_실시간_단가.png",
            mime="image/png",
            use_container_width=True,
            key="today_market_download",
        )
        st.button(
            "단가표 닫기",
            key="today_market_close",
            use_container_width=True,
            on_click=close_today_market,
        )

st.markdown('<div class="search-section-label">메뉴별 추천 원육 검색</div>', unsafe_allow_html=True)

search_input, search_action = st.columns([5, 1.25], gap="small")
with search_input:
    search_query = st.text_input(
        "메뉴 검색",
        placeholder="육회, 돈가스, 삼겹살 검색",
        label_visibility="collapsed"
    )
with search_action:
    st.button("검색", use_container_width=True, type="primary")

matched_key = None

if search_query:
    search_query = search_query.strip()

    for key in expert_db.keys():
        if search_query in key:
            matched_key = key
            break

    if matched_key:
        data = expert_db[matched_key]
        card_data = get_card_data(matched_key)
        market_data = get_geumcheon_market_data(matched_key)
        market_message = (
            "실시간 시세 연동 예정"
            if market_data["market_price"] == "준비중"
            else market_data["market_price"]
        )
        stock_message = (
            "확인 예정"
            if market_data["stock_status"] == "준비중"
            else market_data["stock_status"]
        )
        market_products = market_data.get("products", [])
        if market_products:
            market_items_html = "".join(
                f"<li>{escape(product['label'])} — {product['kg_price']:,.0f}원/kg</li>"
                for product in market_products
            )
            market_content_html = (
                f'<ol class="result-market-list">{market_items_html}</ol>'
                '<div class="result-market-footnote">'
                '금천미트 실시간 조회 · 가격 및 재고는 변동될 수 있습니다.'
                '</div>'
            )
        else:
            market_content_html = f'<div class="result-market-note">{escape(market_message)}</div>'
        st.markdown(f"""
        <div class="result-card">
            <div class="result-hero">
                <div class="result-eyebrow">이 메뉴에는 <span>추천 원육</span></div>
                <div class="result-pick">{data['pro_pick']}</div>
                <div class="result-recommendation">가장 적합한 원육으로 추천합니다.</div>
            </div>
            <div class="result-body">
                <div class="result-priority">
                    <div class="result-priority-item">
                        <div class="result-priority-label">추천 규격</div>
                        <div class="result-priority-value">{card_data['specification']}</div>
                    </div>
                    <div class="result-priority-item">
                        <div class="result-priority-label">실시간 금천미트 시세</div>
                        {market_content_html}
                    </div>
                </div>
                <div class="result-supporting">
                    <div class="result-support-row">
                        <div class="result-support-label">원산지</div>
                        <div class="result-support-value">{card_data['origin']}</div>
                    </div>
                    <div class="result-support-row">
                        <div class="result-support-label">선택 이유</div>
                        <div class="result-support-value">{data['pro_reason']}</div>
                    </div>
                    <div class="result-support-row">
                        <div class="result-support-label">재고 상태</div>
                        <div class="result-support-value result-stock">{stock_message}</div>
                    </div>
                </div>
                <a class="result-kakao" href="https://open.kakao.com/o/sG85euyi" target="_blank" rel="noopener noreferrer">1:1 카카오톡 상담</a>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if market_products:
            price_card_png = create_price_card_png(matched_key, market_products)
            st.download_button(
                "이미지 저장 (PNG)",
                data=price_card_png,
                file_name=f"도토리다판다_{matched_key}_실시간_단가표.png",
                mime="image/png",
                use_container_width=True,
            )
    else:
        st.error("해당 메뉴는 연구소에 없습니다.")

# 가입 및 시세 안내
st.iframe("""
<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<style>
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; background: transparent; }
body {
    font-family: Pretendard, -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo",
                 "Noto Sans KR", "Malgun Gothic", sans-serif;
    color: #171a18;
}
.signup-card {
    width: 100%; padding: 24px 32px 18px; border: 1px solid #e5e1d8;
    border-radius: 12px; background: #ffffff; text-align: center; position: relative;
}
.signup-eyebrow {
    color: #9a7a3d; font-size: 13px; font-weight: 700; letter-spacing: .025em;
}
.signup-name {
    margin: 16px 0 12px; color: #12291f; font-size: 28px; font-weight: 720;
}
.signup-benefit {
    margin: 0 0 16px; color: #606762; font-size: 14px; font-weight: 500;
    line-height: 1.6; letter-spacing: -0.01em;
}
.signup-cta {
    display: flex; align-items: center; justify-content: center; width: 100%;
    min-height: 50px; padding: 0 18px; border: 0; border-radius: 12px;
    background: #173f30; color: #ffffff; font: inherit; font-weight: 700;
    cursor: pointer;
}
.signup-cta:hover, .signup-cta:focus { background: #123326; }
.copy-status {
    position: absolute; left: 50%; bottom: 12px; z-index: 2;
    max-width: calc(100% - 40px); margin: 0; padding: 6px 10px;
    border-radius: 8px; background: #173f30; color: #ffffff;
    font-size: 13px; line-height: 1.4; white-space: nowrap;
    opacity: 0; pointer-events: none;
    transform: translate(-50%, 4px); transition: opacity .15s ease, transform .15s ease;
}
.copy-status.is-visible { opacity: 1; transform: translate(-50%, 0); }
.copy-status.is-error {
    background: #8a3b32; color: #ffffff; font-size: 12px; white-space: normal;
}
@media (max-width: 700px) {
    .signup-card { padding: 22px 20px 16px; }
    .signup-name { margin: 14px 0 10px; }
    .signup-benefit { margin-bottom: 14px; font-size: 13px; }
}
</style>
</head>
<body>
<div class="signup-card">
    <div class="signup-eyebrow">금천미트 가입</div>
    <div class="signup-name">권오현</div>
    <p class="signup-benefit">가입 시 추천인 입력하면 각종 혜택을 안내받을 수 있습니다.</p>
    <button class="signup-cta" type="button">추천인 복사</button>
    <p class="copy-status" role="status" aria-live="polite"></p>
</div>
<script>
const button = document.querySelector('.signup-cta');
const status = document.querySelector('.copy-status');
const copyText = '권오현';

function setStatus(message, state, duration) {
    status.textContent = message;
    status.className = `copy-status is-visible ${state}`;
    clearTimeout(button.copyStatusTimer);
    button.copyStatusTimer = setTimeout(() => {
        status.textContent = '';
        status.className = 'copy-status';
    }, duration);
}

function legacyCopy(text) {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.setAttribute('readonly', '');
    textarea.style.position = 'fixed';
    textarea.style.left = '-9999px';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    textarea.focus();
    textarea.select();
    textarea.setSelectionRange(0, text.length);
    const copied = document.execCommand('copy');
    document.body.removeChild(textarea);
    return copied;
}

button.addEventListener('click', async () => {
    let copied = false;

    if (navigator.clipboard && window.isSecureContext) {
        try {
            await navigator.clipboard.writeText(copyText);
            copied = true;
        } catch (error) {
            copied = false;
        }
    }

    if (!copied) {
        try {
            copied = legacyCopy(copyText);
        } catch (error) {
            copied = false;
        }
    }

    if (copied) {
        setStatus('복사되었습니다.', 'is-success', 1600);
    } else {
        setStatus(
            '복사에 실패했습니다. 이름을 직접 선택해 복사해주세요.',
            'is-error',
            3500
        );
    }
});
</script>
</body>
</html>
""", height=230)

st.markdown("""
<div class='market-container'>
    <a class='market-cta' href='https://www.ekcm.co.kr/' target='_blank'>동원 금천미트 공식몰</a>
</div>
""", unsafe_allow_html=True)

# 카카오톡 상담
st.markdown(f"""
<div class='btn-container'>
    <a href='https://open.kakao.com/o/sG85euyi' class='btn-kakao' target='_blank'>1:1 카카오톡 상담</a>
</div>
""", unsafe_allow_html=True)
