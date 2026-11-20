
import requests
import json

from datasets import load_dataset


# uses AQuA which is based on GRE questions https://arxiv.org/abs/1705.04146
DATASET = load_dataset("deepmind/aqua_rat", "raw")

BASE_URL = "https://pinesat.duckdns.org/api/questions"

DIFFICULTY_MAP = {
    "easy": "easy",
    "medium": "easy",
    "intermediate": "medium",
    "hard": "intermediate"
}

ANSWER_MAP = {"A": 0, "B": 1, "C": 2, "D": 3}

LETTERS = "ABCD"

def huggingface_dataset(row):
    """
    Pulls data from multiple different games from https://huggingface.co/datasets/deepmind/aqua_rat
    and returns it in the desired format

    :param row: a single row of the DATASET
    :return: dict formatted data for questions
    """
    # we don't really care about train/test splits for our purposes so just pulling from the largest section
    #train_data = DATASET['train']
    
    #return json.dumps(train_data)
    #print(train_data["options"])

    choices = {}
    for op in row["options"]:
        try:
            letter, answer = op.split(")", 1)
            choices[letter] = answer

        except ValueError as e:
            print(f"Error: {e}\tOutput: {op}")

    return {
        "id": 0,
        "section": "AQuA",
        "domain": "GRE",
        
        # AQuA questions don't have visuals
        "visuals": {
            "type": "null",
            "svg_content": "null"
        },

        "question": {
            "choices": choices,
            "question": row["question"],
            "paragraph": "null",
            "explanation": row["rationale"],
            "correct_answer": row["correct"]
        },

        "difficulty": "hard"
    }

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
    q = list(load_questions())
    
    # with open("data-files/opensat_questions.json", "w", encoding="utf-8") as f:
    #     json.dump(list(q), f, indent=2, ensure_ascii=False)

    # we don't really care about train/test splits for our purposes so just pulling from the largest section
    data = DATASET['train'].shuffle(seed=42)

    # select 30 random questions
    selected = data.select(range(100))

    for row in selected:
        q.append(huggingface_dataset(row))

    with open("data-files/alldata_questions.json", "w", encoding="utf-8") as f:
        json.dump(q, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()

