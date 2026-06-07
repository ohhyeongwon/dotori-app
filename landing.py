import streamlit as st

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="도토리다판다", layout="wide")
st.markdown("""
    <style>
    .main-title { font-family: sans-serif; font-size: 50px !important; color: #333; text-align: center; margin-top: 20px; }
    .sub-title { font-size: 18px !important; color: #666; text-align: center; margin-bottom: 30px; }
    .highlight-name { font-weight: 800 !important; color: #2E7D32; background-color: #FFF176; padding: 0 5px; }
    .btn-container { display: flex; justify-content: center; gap: 20px; margin-top: 40px; }
    .btn { padding: 15px 30px; border-radius: 50px; font-weight: bold; text-decoration: none; text-align: center; display: inline-block; }
    .kakao { background-color: #FEE500; color: #3c1e1e; }
    </style>
""", unsafe_allow_html=True)

# 2. 데이터베이스 (사장님의 40개 메뉴 로직 유지)
expert_db = {
    # 기존 데이터 유지... (여기에 원래 있던 40개 데이터 넣으시면 됩니다)
}

# 3. 화면 출력
st.markdown('<p class="main-title">도토리다판다</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">사장님의 행복한 하루를 응원합니다 by 권오현</p>', unsafe_allow_html=True)

search_query = st.text_input("📋 궁금한 메뉴를 검색하세요", placeholder="ex) 육회, 삼겹살, 제육볶음...")

if search_query:
    matched_key = next((key for key in expert_db.keys() if search_query in key), None)
    if matched_key:
        data = expert_db[matched_key]
        st.markdown(f"### 🏆 {data['title']}")
        st.write(f"**연구소 의견:** {data['desc']}")
        c1, c2 = st.columns(2)
        with c1:
            for p in data['points']: st.write(f"✅ {p}")
        with c2:
            for part, desc in data['parts'].items(): st.write(f"🔹 {part}: {desc}")
        st.warning(f"🚀 **전문가 공급 전략:** {data['strategy']}")
    else:
        st.error("해당 메뉴는 연구소에 없습니다.")

st.markdown("---")

# 4. 좌우 대칭 및 중앙 정렬 레이아웃
col_a, col_b = st.columns([1, 1])

with col_a:
    st.markdown("<div style='text-align: center;'><h3>📊 실시간 축산 도매 시세</h3></div>", unsafe_allow_html=True)
    with st.expander("📈 시세표 확인 (클릭)"):
        st.image("price.jpg", use_container_width=True) # 경고창 제거

with col_b:
    st.markdown("<div style='text-align: center;'><h3>💡 도매 시세 실시간 조회</h3></div>", unsafe_allow_html=True)
    st.markdown("""
        <div style="text-align: center; line-height: 1.8;">
            회원가입 시 추천인 <span class='highlight-name'>권오현</span>을 입력해주세요.<br>
            매주 유용한 축산 정보를 정기적으로 발송해 드립니다.
        </div>
    """, unsafe_allow_html=True)
    st.write("")
    # 버튼 중앙 배치
    c_btn1, c_btn2, c_btn3 = st.columns([1, 2, 1])
    with c_btn2:
        st.link_button("금천미트몰 바로가기", "https://www.ekcm.co.kr/", use_container_width=True)

# 5. 카카오톡 상담 버튼 복구
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""
    <div class="btn-container">
        <a href="https://open.kakao.com/o/sG85euyi" class="btn kakao">🟡 1:1 카카오톡 무료상담</a>
    </div>
""", unsafe_allow_html=True)
