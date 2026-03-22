# MCQ-Gen — Gen AI multiple-choice quiz generator

Streamlit app that reads **PDF** or **TXT** study material, calls **OpenAI** (`gpt-4o-mini`) via **LangChain** to generate MCQs, shows a short **review** of difficulty/tone, and runs an **interactive quiz** in the browser.

## Setup

Requires **Python 3.8+**. Dependencies use **LangChain 0.2.x** (`langchain-core` / `langchain-openai` / `langchain-community`) so installs succeed on 3.8; the umbrella `langchain` package **0.3+** needs Python **3.9+**, so it is not listed.

1. Create a virtual environment (recommended) and install dependencies:

```text
pip install -r requirements.txt
pip install -e .
```

2. Copy `.env.example` to `.env` and set your API key:

```text
OPENAI_API_KEY=sk-...
```

## Run

From the project root (with the venv activated):

```text
python -m streamlit run App.py
```

Using `python -m streamlit` avoids broken `streamlit.exe` launchers if the project folder was **moved or renamed** after packages were installed (the `.exe` embeds the old path to `python.exe`).

To repair the `streamlit` shortcut instead, reinstall it in the current venv:

```text
python -m pip install --force-reinstall streamlit
```

## Project layout

- `App.py` — Streamlit UI
- `src/mcqgenerator/MCQGenerator.py` — prompts and LLM pipeline (`langchain-core` + `langchain-openai`)
- `src/mcqgenerator/utils.py` — PDF/TXT extraction
- `src/mcqgenerator/logger.py` — file logging under `logs/`

## Notes

- PDFs must contain selectable text; scanned image-only PDFs are not supported without OCR.
- The model is instructed to set each question’s `correct` field to `a`, `b`, `c`, or `d` so scoring matches the UI.
