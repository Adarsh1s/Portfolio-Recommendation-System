"""
Page 2: Risk Questionnaire
7 scored MCQ questions to determine the user's risk profile.
"""

import streamlit as st
from utils.api import get_questions, submit_questionnaire, get_my_profile

st.set_page_config(page_title="Risk Questionnaire | Portfolio System", page_icon="🧠", layout="centered")


def _require_login():
    if not st.session_state.get("token"):
        st.warning("Please log in first.")
        st.switch_page("app.py")


_require_login()

token = st.session_state.token

# Check profile exists
profile = get_my_profile(token)
if not profile:
    st.warning("Please complete your financial profile first.")
    if st.button("Go to Onboarding"):
        st.switch_page("pages/1_Onboarding.py")
    st.stop()

st.title("🧠 Risk Assessment Questionnaire")
st.markdown(
    "Answer 7 questions honestly. Your answers determine your risk profile, "
    "which drives the asset allocation of your portfolio."
)
st.divider()

# Show existing score if already done
if profile.get("risk_score") is not None:
    st.info(
        f"✅ You already have a risk score of **{profile['risk_score']}** "
        f"({profile.get('risk_profile_name', 'Unknown')}). "
        f"Resubmitting will recalculate it."
    )

# Fetch questions from API
with st.spinner("Loading questions…"):
    try:
        questions = get_questions(token)
    except ValueError as e:
        st.error(str(e))
        st.stop()

OPTION_LABELS = {1: "A", 2: "B", 3: "C", 4: "D"}

answers = {}
with st.form("questionnaire_form"):
    for i, q in enumerate(questions):
        st.markdown(f"**Q{i + 1}. {q['question']}**")
        options = q.get("options", {})
        # Sort option keys numerically when possible, then build labeled option strings
        def _opt_sort_key(item):
            k = item[0]
            try:
                return int(k)
            except Exception:
                return str(k)

        sorted_options = sorted(options.items(), key=_opt_sort_key)
        option_list = []
        for k, v in sorted_options:
            try:
                label = OPTION_LABELS[int(k)]
            except Exception:
                label = str(k)
            option_list.append(f"{label}) {v}")

        default_index = 1 if len(option_list) > 1 else 0
        selected = st.radio(
            label=f"q{q.get('question_id')}",
            options=option_list,
            label_visibility="collapsed",
            index=default_index,
            key=f"q_{q.get('question_id')}",
        )

        # Map letter label back to score integer (A=1, B=2, C=3, D=4)
        letter_to_int = {"A": 1, "B": 2, "C": 3, "D": 4}
        selected_letter = selected[0] if isinstance(selected, str) and len(selected) > 0 else selected
        try:
            qid = int(q.get("question_id")) if isinstance(q.get("question_id"), str) and q.get("question_id").isdigit() else q.get("question_id")
        except Exception:
            qid = q.get("question_id")

        answers[qid] = letter_to_int.get(selected_letter)
        st.divider()

    submitted = st.form_submit_button(
        "Submit Questionnaire →",
        use_container_width=True, type="primary",
    )

if submitted:
    answer_payload = [
        {"question_id": qid, "answer": ans}
        for qid, ans in answers.items()
    ]
    with st.spinner("Calculating your risk profile…"):
        try:
            result = submit_questionnaire(token, answer_payload)
            score       = result["risk_score"]
            profile_name = result["profile_name"]
            description  = result["description"]

            # Score bar visual
            st.success(f"Your Risk Score: **{score}/100** → **{profile_name}**")

            # Progress bar (0–100)
            col1, col2 = st.columns([3, 1])
            with col1:
                st.progress(score / 100)
            with col2:
                st.metric("Score", score)

            st.info(description)

            # Update session if name stored
            st.session_state["risk_profile"] = profile_name
            st.session_state["risk_score"]   = score

            st.balloons()

            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("Generate My Portfolio →", type="primary", use_container_width=True):
                    st.switch_page("pages/3_Dashboard.py")
            with col_b:
                if st.button("Retake Questionnaire", use_container_width=True):
                    st.rerun()

        except ValueError as e:
            st.error(str(e))
