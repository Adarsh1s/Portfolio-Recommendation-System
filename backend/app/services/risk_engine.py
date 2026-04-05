"""
Risk Scoring Engine
-------------------
7 MCQ questions, each scored 1–4 (4 = highest risk appetite).
Max raw score = 28. Normalized to 0–100 scale.

Questions cover:
  Q1 - Primary investment goal
  Q2 - Reaction to 20% portfolio drop
  Q3 - Investment time horizon
  Q4 - Income stability
  Q5 - Market knowledge / experience
  Q6 - Acceptable annual loss
  Q7 - Emergency fund adequacy
"""

from app.schemas.schemas import QuestionnaireAnswer

# Score weights per question (some questions matter more)
QUESTION_WEIGHTS = {
    1: 1.0,   # Goal
    2: 1.5,   # Reaction to loss — highest weight
    3: 1.2,   # Time horizon
    4: 0.8,   # Income stability
    5: 1.0,   # Market knowledge
    6: 1.5,   # Acceptable loss — highest weight
    7: 1.0,   # Emergency fund
}

MAX_RAW_SCORE = sum(4 * w for w in QUESTION_WEIGHTS.values())  # 4 = max per question


def calculate_risk_score(answers: list[QuestionnaireAnswer]) -> int:
    """
    Returns a risk score from 0 to 100.
    Higher score = more aggressive risk profile.
    """
    if len(answers) != 7:
        raise ValueError(f"Expected 7 answers, got {len(answers)}")

    answer_map = {a.question_id: a.answer for a in answers}

    raw = 0.0
    for qid, weight in QUESTION_WEIGHTS.items():
        ans = answer_map.get(qid)
        if ans is None:
            raise ValueError(f"Missing answer for question {qid}")
        if ans not in (1, 2, 3, 4):
            raise ValueError(f"Answer for Q{qid} must be 1–4, got {ans}")
        raw += ans * weight

    # Normalize to 0–100
    score = round((raw / MAX_RAW_SCORE) * 100)
    return max(0, min(100, score))


QUESTIONNAIRE_DEFINITIONS = [
    {
        "question_id": 1,
        "question":    "What is your primary investment goal?",
        "options": {
            1: "Preserve capital — I cannot afford to lose money",
            2: "Generate regular income with minimal risk",
            3: "Balanced growth with moderate risk",
            4: "Maximize long-term wealth growth",
        },
    },
    {
        "question_id": 2,
        "question":    "If your portfolio dropped 20% in 3 months, what would you do?",
        "options": {
            1: "Sell everything immediately to stop further losses",
            2: "Sell some and move to safer investments",
            3: "Hold and wait for recovery",
            4: "Buy more to take advantage of lower prices",
        },
    },
    {
        "question_id": 3,
        "question":    "How long do you plan to stay invested?",
        "options": {
            1: "Less than 2 years",
            2: "2 to 5 years",
            3: "5 to 10 years",
            4: "More than 10 years",
        },
    },
    {
        "question_id": 4,
        "question":    "How stable is your monthly income?",
        "options": {
            1: "Very unstable — irregular freelance / self-employed",
            2: "Somewhat variable — bonus-heavy structure",
            3: "Mostly stable with occasional variability",
            4: "Very stable — salaried with guaranteed income",
        },
    },
    {
        "question_id": 5,
        "question":    "How would you describe your investment knowledge?",
        "options": {
            1: "Beginner — I know very little about investing",
            2: "Basic — I understand FDs, PPF, and mutual funds",
            3: "Intermediate — I follow markets and understand equity",
            4: "Advanced — I actively manage my portfolio",
        },
    },
    {
        "question_id": 6,
        "question":    "What is the maximum annual loss you could accept without panic?",
        "options": {
            1: "0% — I cannot tolerate any loss",
            2: "Up to 5% loss is acceptable",
            3: "Up to 15% loss is acceptable",
            4: "More than 15% loss is fine for long-term gains",
        },
    },
    {
        "question_id": 7,
        "question":    "Do you have an emergency fund covering 6+ months of expenses?",
        "options": {
            1: "No emergency fund at all",
            2: "Partial — covers 1–2 months",
            3: "Covers 3–5 months",
            4: "Yes — fully funded, 6+ months covered",
        },
    },
]
