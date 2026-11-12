
import time
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="학생 학습 플래너",
    page_icon="📚",
    layout="centered",
)

# ----------------------------
# 세션 상태 초기화
# ----------------------------
defaults = {
    "subjects": ["국어", "영어", "수학", "과학"],
    "totals": {},
    "selected_subject": "국어",
    "running": False,
    "started_at": None,
    "elapsed_before_start": 0,
    "todo_list": [],
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value.copy() if isinstance(value, (dict, list)) else value

for subject in st.session_state.subjects:
    st.session_state.totals.setdefault(subject, 0)

# ----------------------------
# 사이드바 메뉴
# ----------------------------
st.sidebar.title("📚 학습 플래너")

page = st.sidebar.radio(
    "메뉴",
    ["공부타이머", "오늘 할일", "공부회고"],
)

# ----------------------------
# 타이머 함수
# ----------------------------
def format_time(seconds):
    seconds = max(0, int(seconds))
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def current_elapsed():
    elapsed = st.session_state.elapsed_before_start
    if st.session_state.running and st.session_state.started_at is not None:
        elapsed += time.time() - st.session_state.started_at
    return int(elapsed)


# ----------------------------
# 1. 공부타이머
# ----------------------------
if page == "공부타이머":

    st.title("⏱️ 공부타이머")
    st.caption("과목별 공부 시간을 측정하고 기록해 보세요.")

    st.subheader("과목")

    selected = st.selectbox(
        "공부할 과목을 선택하세요",
        st.session_state.subjects,
        index=(
            st.session_state.subjects.index(st.session_state.selected_subject)
            if st.session_state.selected_subject in st.session_state.subjects
            else 0
        ),
        disabled=st.session_state.running,
    )

    st.session_state.selected_subject = selected

    with st.expander("과목 추가하기"):
        new_subject = st.text_input(
            "새 과목 이름",
            placeholder="예: 한국사",
            key="new_subject_input",
        )

        if st.button("과목 추가", use_container_width=True):
            name = new_subject.strip()

            if not name:
                st.warning("과목 이름을 입력해 주세요.")

            elif name in st.session_state.subjects:
                st.info("이미 등록된 과목입니다.")

            else:
                st.session_state.subjects.append(name)
                st.session_state.totals[name] = 0
                st.session_state.selected_subject = name
                st.rerun()

    st.divider()
    st.subheader("학습 타이머")

    @st.fragment(run_every="1s")
    def timer_display():

        elapsed = current_elapsed()

        status = (
            "측정 중"
            if st.session_state.running
            else "일시정지"
        )

        st.markdown(
            f"""
            <div style="
                background: linear-gradient(135deg, #172554, #1e40af);
                color: white;
                padding: 28px 16px;
                border-radius: 18px;
                text-align: center;
                margin: 8px 0 18px 0;
            ">
                <div style="font-size: 14px; opacity: 0.85;">
                    현재 과목 · {st.session_state.selected_subject}
                </div>

                <div style="
                    font-size: clamp(42px, 10vw, 64px);
                    font-weight: 700;
                    font-variant-numeric: tabular-nums;
                    letter-spacing: 2px;
                ">
                    {format_time(elapsed)}
                </div>

                <div style="font-size: 13px; opacity: 0.8;">
                    {status}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    timer_display()

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button(
            "▶ 시작",
            type="primary",
            use_container_width=True,
            disabled=st.session_state.running,
        ):
            st.session_state.running = True
            st.session_state.started_at = time.time()
            st.rerun()

    with col2:
        if st.button(
            "⏸ 일시정지",
            use_container_width=True,
            disabled=not st.session_state.running,
        ):
            st.session_state.elapsed_before_start = current_elapsed()
            st.session_state.running = False
            st.session_state.started_at = None
            st.rerun()

    with col3:
        if st.button("↺ 초기화", use_container_width=True):
            st.session_state.running = False
            st.session_state.started_at = None
            st.session_state.elapsed_before_start = 0
            st.rerun()

    st.caption(
        "초기화는 현재 타이머만 초기화합니다. "
        "과목별 누적 기록은 유지됩니다."
    )

    st.divider()
    st.subheader("과목별 학습 기록")

    display_totals = dict(st.session_state.totals)

    if st.session_state.running:
        subject = st.session_state.selected_subject

        display_totals[subject] = (
            display_totals.get(subject, 0) + current_elapsed()
        )

    rows = [
        {
            "과목": subject,
            "누적 학습 시간": format_time(seconds),
            "초": int(seconds),
        }
        for subject, seconds in display_totals.items()
    ]

    df = pd.DataFrame(rows)

    if df.empty:
        st.info("아직 기록된 학습 시간이 없습니다.")

    else:
        st.dataframe(
            df[["과목", "누적 학습 시간"]],
            hide_index=True,
            use_container_width=True,
        )

        total_seconds = sum(display_totals.values())

        st.metric(
            "총 학습 시간",
            format_time(total_seconds),
        )

        csv = df[["과목", "누적 학습 시간", "초"]].to_csv(
            index=False
        ).encode("utf-8-sig")

        st.download_button(
            "기록을 CSV로 다운로드",
            data=csv,
            file_name="study_time_records.csv",
            mime="text/csv",
            use_container_width=True,
        )

    st.caption(
        "※ 기록은 현재 브라우저 세션에 저장됩니다. "
        "앱 세션이 종료되면 초기화될 수 있습니다."
    )


# ----------------------------
# 2. 오늘 할일
# ----------------------------
elif page == "오늘 할일":

    st.title("📝 오늘 할일")
    st.caption("오늘 해야 할 공부를 과목별로 정리해 보세요.")

    st.divider()

    st.subheader("할 일 추가하기")

    with st.form("todo_form", clear_on_submit=True):

        subject = st.selectbox(
            "과목",
            st.session_state.subjects,
        )

        task = st.text_input(
            "할 일",
            placeholder="예: 수학 문제집 20문제 풀기",
        )

        submitted = st.form_submit_button(
            "➕ 추가",
            use_container_width=True,
        )

        if submitted:

            if task.strip():

                st.session_state.todo_list.append({
                    "subject": subject,
                    "task": task.strip(),
                    "done": False,
                })

                st.success("할 일이 추가되었습니다!")
                st.rerun()

            else:
                st.warning("할 일을 입력해 주세요.")

    st.divider()

    st.subheader("오늘의 할 일 목록")

    if not st.session_state.todo_list:

        st.info("아직 등록된 할 일이 없습니다.")

    else:

        for i, item in enumerate(st.session_state.todo_list):

            col1, col2 = st.columns([5, 1])

            with col1:

                checked = st.checkbox(
                    f"**[{item['subject']}]** {item['task']}",
                    value=item["done"],
                    key=f"todo_check_{i}",
                )

                st.session_state.todo_list[i]["done"] = checked

            with col2:

                if st.button(
                    "삭제",
                    key=f"todo_delete_{i}",
                    use_container_width=True,
                ):

                    st.session_state.todo_list.pop(i)
                    st.rerun()

        total = len(st.session_state.todo_list)

        completed = sum(
            1 for item in st.session_state.todo_list
            if item["done"]
        )

        st.divider()

        st.metric(
            "완료한 할 일",
            f"{completed} / {total}",
        )


# ----------------------------
# 3. 공부회고
# ----------------------------
elif page == "공부회고":

    st.title("📖 공부회고")
