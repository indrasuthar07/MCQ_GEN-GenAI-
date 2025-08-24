import streamlit as st
import pandas as pd
import json
from src.mcqgenerator.MCQGenerator import generate_evaluate_chain
from langchain.callbacks import get_openai_callback
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Streamlit app title
st.title("MCQ Generator & Quiz")

# File uploader
uploaded_file = st.file_uploader("Upload a PDF or Text file", type=["pdf", "txt"])

# Input fields for MCQ generation
number_of_questions = st.number_input("Number of Questions", min_value=1, max_value=100, value=5)
subject = st.text_input("Subject", "Maths")
tone = st.selectbox("Tone", ["Simple", "Formal", "Casual"])

# Initialize session state for quiz data and user answers
if 'quiz_data' not in st.session_state:
    st.session_state.quiz_data = None
if 'user_answers' not in st.session_state:
    st.session_state.user_answers = {}
if 'quiz_submitted' not in st.session_state:
    st.session_state.quiz_submitted = False

# Generate MCQs button
if st.button("Generate MCQs"):
    if uploaded_file is not None:
        # Read the content from the uploaded file
        text = uploaded_file.read().decode("utf-8") if uploaded_file.name.endswith(".txt") else "PDF content extraction not implemented yet."
        
        # Prepare the response JSON structure
        RESPONSE_JSON = {
            "1": {
                "mcq": "multiple choice question",
                "options": {
                    "a": "choice here",
                    "b": "choice here",
                    "c": "choice here",
                    "d": "choice here",
                },
                "correct": "correct answer",
            },
        }

        # Generate MCQs
        with get_openai_callback() as cb:
            response = generate_evaluate_chain({
                "text": text,
                "number": number_of_questions,
                "subject": subject,
                "tone": tone,
                "response_json": json.dumps(RESPONSE_JSON)
            })

        # Process the response
        quiz = response.get("quiz")
        quiz = json.loads(quiz)
        
        # Store quiz data in session state
        st.session_state.quiz_data = quiz
        st.session_state.user_answers = {}
        st.session_state.quiz_submitted = False
        
        st.success("MCQs generated successfully! Scroll down to take the quiz.")
    else:
        st.error("Please upload a valid file.")

# Display interactive quiz if quiz data exists
if st.session_state.quiz_data:
    st.markdown("---")
    st.header("Take the Quiz")
    
    # Create form for quiz
    with st.form("quiz_form"):
        for question_num, question_data in st.session_state.quiz_data.items():
            st.markdown(f"**Question {question_num}:** {question_data['mcq']}")
            
            # Create radio buttons for options with no default selection
            options = list(question_data['options'].keys())
            user_answer = st.radio(
                "",
                options,
                key=f"q{question_num}",
                format_func=lambda x: f"{x}: {question_data['options'][x]}",
                index=None  # No default selection
            )
            
            # Store user answer
            st.session_state.user_answers[question_num] = user_answer
        
        # Submit button
        submitted = st.form_submit_button("Submit Quiz")
        
        if submitted:
            st.session_state.quiz_submitted = True

# Display results after submission
if st.session_state.quiz_submitted and st.session_state.quiz_data:
    st.markdown("---")
    st.header("Quiz Results")
    
    correct_count = 0
    total_questions = len(st.session_state.quiz_data)
    
    for question_num, question_data in st.session_state.quiz_data.items():
        user_answer = st.session_state.user_answers[question_num]
        correct_answer = question_data['correct']
        
        st.markdown(f"**Question {question_num}:** {question_data['mcq']}")
        
        if user_answer == correct_answer:
            st.success(f"✅ Your answer: {user_answer} - Correct!")
            correct_count += 1
        else:
            st.error(f"❌ Your answer: {user_answer} - Wrong! Correct answer: {correct_answer}")
        
        # Show all options with correct answer highlighted
        options_text = ""
        for option, option_text in question_data['options'].items():
            if option == correct_answer:
                options_text += f"**{option}: {option_text} ✓**  \n"
            else:
                options_text += f"{option}: {option_text}  \n"
        
        st.markdown(options_text)
        st.markdown("---")
    
    # Display final score
    st.header(f"Final Score: {correct_count}/{total_questions}")
    st.metric("Correct Answers", correct_count)
    st.metric("Wrong Answers", total_questions - correct_count)
    st.metric("Percentage", f"{(correct_count/total_questions)*100:.1f}%")
    
    # Reset button
    if st.button("Take Quiz Again"):
        st.session_state.quiz_submitted = False
        st.session_state.user_answers = {}
        st.rerun()
