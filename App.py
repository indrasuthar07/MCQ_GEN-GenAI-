import json
import os

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

try:
    from langchain_community.callbacks import get_openai_callback
except ImportError:  # pragma: no cover
    get_openai_callback = None

from src.mcqgenerator.MCQGenerator import generate_evaluate_chain
from src.mcqgenerator.utils import read_file

st.set_page_config(page_title="MCQ Generator & Quiz", layout="wide")

st.title("MCQ Generator & Quiz")
st.caption("Upload study material (PDF or TXT) and generate multiple-choice questions with an OpenAI model.")

uploaded_file = st.file_uploader("Upload a PDF or Text file", type=["pdf", "txt"])

number_of_questions = st.number_input("Number of Questions", min_value=1, max_value=100, value=5)
subject = st.text_input("Subject", "General")
tone = st.selectbox("Tone", ["Simple", "Formal", "Casual"])

if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = None
if "user_answers" not in st.session_state:
    st.session_state.user_answers = {}
if "quiz_submitted" not in st.session_state:
    st.session_state.quiz_submitted = False
if "last_review" not in st.session_state:
    st.session_state.last_review = None

if not os.getenv("OPENAI_API_KEY", "").strip():
    st.warning("Set **OPENAI_API_KEY** in a `.env` file in this folder (or in your environment) before generating MCQs.")

if st.button("Generate MCQs"):
    if uploaded_file is None:
        st.error("Please upload a valid file.")
    else:
        try:
            text = read_file(uploaded_file)
        except (RuntimeError, ValueError) as e:
            st.error(str(e))
            text = None

        if text is not None:
            if len(text.strip()) < 50:
                st.error("The uploaded content is too short. Add more text or a longer document.")
            else:
                response_json_template = {
                    "1": {
                        "mcq": "multiple choice question",
                        "options": {
                            "a": "choice here",
                            "b": "choice here",
                            "c": "choice here",
                            "d": "choice here",
                        },
                        "correct": "a",
                    },
                }

                payload = {
                    "text": text,
                    "number": int(number_of_questions),
                    "subject": subject,
                    "tone": tone,
                    "response_json": json.dumps(response_json_template),
                }

                try:
                    if get_openai_callback is not None:
                        with get_openai_callback() as cb:
                            response = generate_evaluate_chain(payload)
                        st.caption(
                            f"Tokens — prompt: {cb.prompt_tokens}, completion: {cb.completion_tokens}, "
                            f"total: {cb.total_tokens}, cost (USD): ${cb.total_cost:.4f}"
                        )
                    else:
                        response = generate_evaluate_chain(payload)
                except ValueError as e:
                    st.error(str(e))
                    response = None
                except Exception as e:
                    st.error(f"Generation failed: {e}")
                    response = None

                if response:
                    try:
                        quiz = json.loads(response["quiz"])
                    except json.JSONDecodeError as e:
                        st.error(f"Model returned invalid JSON: {e}")
                        quiz = None

                    if quiz:
                        st.session_state.quiz_data = quiz
                        st.session_state.user_answers = {}
                        st.session_state.quiz_submitted = False
                        st.session_state.last_review = response.get("review")
                        st.success("MCQs generated successfully! Scroll down to take the quiz.")
                        if st.session_state.last_review:
                            with st.expander("Quiz review (complexity / tone notes)"):
                                st.write(st.session_state.last_review)

if st.session_state.quiz_data:
    st.markdown("---")
    st.header("Take the Quiz")

    with st.form("quiz_form"):
        for question_num, question_data in st.session_state.quiz_data.items():
            st.markdown(f"**Question {question_num}:** {question_data['mcq']}")
            options = list(question_data["options"].keys())
            st.radio(
                "Select an answer",
                options,
                key=f"q{question_num}",
                format_func=lambda x, qd=question_data: f"{x}: {qd['options'][x]}",
                index=None,
                label_visibility="collapsed",
            )

        submitted = st.form_submit_button("Submit Quiz")

        if submitted:
            for question_num in st.session_state.quiz_data:
                st.session_state.user_answers[question_num] = st.session_state.get(f"q{question_num}")
            st.session_state.quiz_submitted = True

if st.session_state.quiz_submitted and st.session_state.quiz_data:
    st.markdown("---")
    st.header("Quiz Results")

    correct_count = 0
    total_questions = len(st.session_state.quiz_data)

    for question_num, question_data in st.session_state.quiz_data.items():
        user_answer = st.session_state.user_answers.get(question_num)
        correct_answer = str(question_data["correct"]).strip().lower()

        st.markdown(f"**Question {question_num}:** {question_data['mcq']}")

        if user_answer is None:
            st.warning("No answer selected for this question.")
        elif str(user_answer).strip().lower() == correct_answer:
            st.success(f"Your answer: {user_answer} — correct.")
            correct_count += 1
        else:
            st.error(f"Your answer: {user_answer} — incorrect. Correct answer: {correct_answer}")

        options_text = ""
        for option, option_text in question_data["options"].items():
            if str(option).strip().lower() == correct_answer:
                options_text += f"**{option}: {option_text}** ✓  \n"
            else:
                options_text += f"{option}: {option_text}  \n"

        st.markdown(options_text)
        st.markdown("---")

    st.header(f"Final Score: {correct_count}/{total_questions}")
    st.metric("Correct Answers", correct_count)
    st.metric("Wrong Answers", total_questions - correct_count)
    pct = (correct_count / total_questions * 100) if total_questions else 0.0
    st.metric("Percentage", f"{pct:.1f}%")

    if st.button("Take Quiz Again"):
        st.session_state.quiz_submitted = False
        st.session_state.user_answers = {}
        st.rerun()
