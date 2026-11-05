
import requests
import json


BASE_URL = "https://pinesat.duckdns.org/api/questions"

DIFFICULTY_MAP = {
    "easy": "easy",
    "medium": "intermediate",
    "intermediate": "intermediate",
    "hard": "hard"
}

ANSWER_MAP = {"A": 0, "B": 1, "C": 2, "D": 3}

LETTERS = "ABCD"


def make_question_req(section="english", limit=10, domain=None):
    """
    Pull from the API

    note - the limit is only enforced when the domain is specified
    
    :param section: Description
    :param limit: Description
    :param domain: Description
    """
    params = {
        "section": section,
        "limit": limit
    }

    if domain:
        params["domain"] = domain

    response = requests.get(
        BASE_URL,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    return response.json()

def normalize_opensat_question(item, section):
    """
    Normalizes the questions from OpenSAT to be usable in this app
    
    :param item: individual entry in the database
    :param section: SAT section title (english/math)
    """
    q = item.get("question", {})

    passage = q.get("paragraph") or ""
    question_text = q.get("question") or ""

    # get difficulty from the API response
    raw_difficulty = (
        item.get("difficulty")
        or q.get("difficulty")
        or "medium"
    )

    difficulty = DIFFICULTY_MAP.get(
        str(raw_difficulty).lower(),
        "intermediate"
    )

    raw_choices = q.get("choices", {})

    choices = {}
    if isinstance(choices, dict):
        for letter, answer in raw_choices.items():
            choices[str(letter)] = str(answer)

    return {
        "id": item.get("id"),
        "section": section,
        "domain": item.get("domain", ""),

        "visuals": item.get("visuals", {
            "type": "null",
            "svg_content": "null"
        }),

        "question": {
            "choices": q.get("choices", {}),
            "question": q.get("question", ""),
            "paragraph": q.get("paragraph", ""),
            "explanation": q.get("explanation", ""),
            "correct_answer": q.get("correct_answer")
        },

        "difficulty": difficulty
    }

def load_questions(question_total = 100):
    """
    Docstring for load_questions
    
    :param question_total: Specifies the number of questions to be pulled from the API
    """
    math_questions = make_question_req(
        section="MATH",
        limit=question_total//2
    )

    # get an equal amount of english questions
    english_questions = make_question_req(
        section="english",
        limit=question_total//2
    )

    # combine the two and normalize the db entries
    questions = []
    for item in math_questions:
        questions.append(normalize_opensat_question(item, "math"))
        
    for item in english_questions:
        questions.append(normalize_opensat_question(item, "english"))

    return questions

def main():
    q = load_questions()
    
    with open("data-files/opensat_questions.json", "w", encoding="utf-8") as f:
        json.dump(q, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()

