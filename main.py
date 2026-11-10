
import streamlit as st
import time
import pandas as pd
from datetime import datetime

# 페이지 설정
st.set_page_config(
    page_title="학생 학습 타이머",
    page_icon="📚",
    layout="centered"
)

# 세션 상태 초기화
defaults = {
    "running": False,
    "start_time": None,
    "elapsed": 0.0,
    "active_subject": None,
    "subjects": ["국어", "영어", "수학", "과학", "사회"],
    "records": [],
    "logged_elapsed": 0.0
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


def format_time(seconds):
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def get_elapsed():
    elapsed = st.session_state.elapsed

    if st.session_state.running:
        elapsed += time.time() - st.session_state.start_time

    return elapsed


def save_record(seconds):
    if seconds <= 0 or not st.session_state.active_subject:
        return

    st.session_state.records.append({
        "날짜": datetime.now().strftime("%Y-%m-%d"),
        "과목": st.session_state.active_subject,
        "공부 시간(초)": int(seconds),
        "공부 시간": format_time(seconds)
    })


st.title("📚 학생 학습 타이머")
st.caption("과목별 공부 시간을 기록하고 관리하세요.")

# 과목 선택
st.subheader("📖 공부할 과목 선택")

new_subject = st.text_input(
    "새 과목 추가",
    placeholder="과목명을 입력하세요"
)

if st.button("과목 추가"):
    if new_subject.strip():
        if new_subject.strip() not in st.session_state.subjects:
            st.session_state.subjects.append(new_subject.strip())
            st.success("과목이 추가되었습니다.")
        else:
            st.warning("이미 등록된 과목입니다.")

subject = st.selectbox(
    "과목",
    st.session_state.subjects,
    disabled=st.session_state.running
)

st.divider()

# 타이머 영역
st.subheader("⏱️ 학습 타이머")

if not st.session_state.running and st.session_state.elapsed == 0:
    st.session_state.active_subject = subject

current_subject = (
    st.session_state.active_subject
    or subject
)

if st.session_state.running:
    current_time = get_elapsed()
else:
    current_time = st.session_state.elapsed

st.markdown(
    f"""
    <div style="
        background-color:#1E293B;
        padding:35px;
        border-radius:15px;
        text-align:center;
        color:white;">
        <div style="font-size:18px;">현재 공부 과목</div>
        <div style="font-size:24px;font-weight:bold;">
            {current_subject}
        </div>
        <div style="
            font-size:52px;
            font-weight:bold;
            margin-top:15px;">
            {format_time(current_time)}
        </div>
        <div style="color:#CBD5E1;">
            {"공부 진행 중" if st.session_state.running else "일시정지"}
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

st.write("")

# 버튼 영역
col1, col2, col3 = st.columns(3)

with col1:
    if st.button(
        "▶ 시작",
        use_container_width=True,
        disabled=st.session_state.running
    ):
        if st.session_state.elapsed == 0:
            st.session_state.active_subject = subject

        st.session_state.start_time = time.time()
        st.session_state.running = True
        st.rerun()

with col2:
    if st.button(
        "⏸ 일시정지",
        use_container_width=True,
        disabled=not st.session_state.running
    ):
        now = time.time()
        total = now - st.session_state.start_time

        # 이번 실행 구간을 기록
        segment = total
        save_record(segment)

        st.session_state.elapsed += total
        st.session_state.logged_elapsed += total
        st.session_state.running = False
        st.session_state.start_time = None
        st.rerun()

with col3:
    if st.button("🔄 초기화", use_container_width=True):
        st.session_state.running = False
        st.session_state.start_time = None
        st.session_state.elapsed = 0.0
        st.session_state.logged_elapsed = 0.0
        st.session_state.active_subject = None
        st.rerun()


# 실시간 타이머 갱신
@st.fragment(run_every="1s")
def live_timer():
    if st.session_state.running:
        elapsed = get_elapsed()

        st.caption(
            f"⏱️ 현재 {format_time(elapsed)} 공부 중입니다."
        )

live_timer()

st.divider()

# 공부 기록 영역
st.subheader("📊 과목별 공부 기록")

if st.session_state.records:
    df = pd.DataFrame(st.session_state.records)

    summary = df.groupby("과목")["공부 시간(초)"].sum()

    # 현재 공부 중인 시간도 합산
    if st.session_state.active_subject:
        current = get_elapsed()
        summary[st.session_state.active_subject] = (
            summary.get(st.session_state.active_subject, 0)
            + current
        )

    total_seconds = sum(summary)

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "총 공부 시간",
            format_time(total_seconds)
        )

    with col2:
        st.metric(
            "공부한 과목",
            f"{len(summary)}개"
        )

    st.write("### 과목별 공부 시간")

    chart_df = pd.DataFrame({
        "과목": summary.index,
        "공부 시간(분)": summary.values / 60
    })

    st.bar_chart(
        chart_df,
        x="과목",
        y="공부 시간(분)"
    )

    st.write("### 상세 학습 기록")

    st.dataframe(
        df[["날짜", "과목", "공부 시간"]],
        use_container_width=True,
        hide_index=True
    )

    csv = df.to_csv(index=False).encode("utf-8-sig")

    st.download_button(
        "📥 공부 기록 CSV 다운로드",
        data=csv,
        file_name="study_records.csv",
        mime="text/csv",
        use_container_width=True
    )

else:
    st.info("아직 공부 기록이 없습니다. 타이머를 시작해 보세요!")

st.divider()

st.caption("학생 학습 타이머 | Streamlit 기반 공부 시간 관리")
