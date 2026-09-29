# Incident Response Agent (Hindsight)

An on-call assistant that remembers past incidents, root causes and which fixes worked.

## Setup
1. `pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and fill in Hindsight + Groq credentials
3. `python scripts/load_data.py`  (loads past incidents into Hindsight)
4. `streamlit run app.py`

## How Hindsight is used
- **Retain:** every resolved incident and every engineer feedback (worked/failed).
- **Recall:** on each new alert, the most similar past incidents are recalled and given to the LLM.
- **Reflect:** the sidebar button asks Hindsight to synthesise recurring patterns across incidents.
- **Before/after:** the sidebar toggle turns memory off to show the generic answer.
