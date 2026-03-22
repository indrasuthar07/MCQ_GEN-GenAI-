import json
import logging
import os
import re

import src.mcqgenerator.logger  # noqa: F401 — configures log files on import
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

load_dotenv()


def _require_api_key() -> str:
    key = os.getenv("OPENAI_API_KEY")
    if not key or not key.strip():
        raise ValueError(
            "OPENAI_API_KEY is missing. Add it to a .env file in the project root "
            "or set it in your environment."
        )
    return key.strip()


def _extract_json_object(text: str) -> str:
    """Return a JSON object string from model output (handles ```json fences)."""
    if not text:
        raise ValueError("Empty model response for quiz JSON.")
    t = text.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", t, re.IGNORECASE)
    if fence:
        t = fence.group(1).strip()
    start = t.find("{")
    end = t.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("Could not find a JSON object in the model response.")
    return t[start : end + 1]


def _get_llm() -> ChatOpenAI:
    # langchain-openai 0.1.x (Python 3.8–friendly) uses openai_api_key / model_name.
    return ChatOpenAI(
        openai_api_key=_require_api_key(),
        model_name="gpt-4o-mini",
        temperature=0.7,
    )


QUIZ_TEMPLATE = """Text:
{text}

You are an expert MCQ maker. Given the above text, it is your job to create a quiz of {number} multiple choice questions for {subject} students in {tone} tone.
Make sure the questions are not repeated and check all the questions to be conforming the text as well.
Make sure to format your response like RESPONSE_JSON below and use it as a guide.
Ensure to make {number} MCQs.

IMPORTANT: For each question, the "correct" field must be exactly one of the option keys: "a", "b", "c", or "d" (lowercase), matching the correct choice.

### RESPONSE_JSON
{response_json}
"""

REVIEW_TEMPLATE = """You are an expert English grammarian and writer. Given a Multiple Choice Quiz for {subject} students.
You need to evaluate the complexity of the question and give a complete analysis of the quiz. Only use at max 50 words for complexity analysis.
If the quiz is not at par with the cognitive and analytical abilities of the students, note which questions need to be changed and how the tone could be adjusted.

Quiz_MCQs:
{quiz}

Check from an expert English Writer of the above quiz:
"""

_quiz_prompt = ChatPromptTemplate.from_template(QUIZ_TEMPLATE)
_review_prompt = ChatPromptTemplate.from_template(REVIEW_TEMPLATE)


def generate_evaluate_chain(inputs: dict) -> dict:
    """
    Run quiz generation then a short review. Returns keys: quiz (JSON string), review (str).
    Compatible with LangChain 1.x (no LLMChain / SequentialChain).
    """
    llm = _get_llm()
    try:
        quiz_msg = (_quiz_prompt | llm).invoke(
            {
                "text": inputs["text"],
                "number": inputs["number"],
                "subject": inputs["subject"],
                "tone": inputs["tone"],
                "response_json": inputs["response_json"],
            }
        )
        raw_quiz = quiz_msg.content if hasattr(quiz_msg, "content") else str(quiz_msg)
        quiz_json_str = _extract_json_object(raw_quiz)
        json.loads(quiz_json_str)  # validate before returning

        review_msg = (_review_prompt | llm).invoke(
            {"subject": inputs["subject"], "quiz": quiz_json_str}
        )
        review_text = review_msg.content if hasattr(review_msg, "content") else str(review_msg)

        logging.info("MCQ generation and review completed successfully.")
        return {"quiz": quiz_json_str, "review": review_text}
    except Exception as e:
        logging.exception("generate_evaluate_chain failed: %s", e)
        raise
