from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import re, requests

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def parse_questions(file_path="text.txt"):
    questions = {}
    with open(file_path, "r") as f:
        content = f.read().strip()
    blocks = re.split(r"\n\s*\n", content)  # split by blank lines
    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 3:
            continue
        role = lines[0].strip().lower()
        mode = lines[1].strip().lower()
        qs = [q.strip() for q in lines[2:] if q.strip()]
        if role not in questions:
            questions[role] = {}
        questions[role][mode] = qs
    return questions

QUESTIONS = parse_questions()

import json

def ask_llama(prompt: str, model: str = "llama3") -> str:
    """
    Calls Ollama locally using REST API and collects full response text.
    """
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": model, "prompt": prompt},
            stream=True,   # ✅ get response line by line
            timeout=120
        )
        response.raise_for_status()

        output = ""
        for line in response.iter_lines():
            if not line:
                continue
            try:
                obj = json.loads(line.decode("utf-8"))
                if "response" in obj:
                    output += obj["response"]
            except Exception as e:
                print("Parse error:", e)
                continue
        return output.strip()
    except Exception as e:
        print("Error running LLaMA:", e)
        return "Error: Could not get model feedback.\nScore: 0"
@app.post("/start_interview")
async def start_interview(request: Request):
    data = await request.json()
    role = data.get("role", "").strip().lower()
    mode = data.get("mode", "").strip().lower()
    if role not in QUESTIONS or mode not in QUESTIONS[role]:
        return {"question": None, "error": "Role or mode is invalid."}
    questions = QUESTIONS[role][mode]
    return {"question": questions[0] if questions else None}

@app.post("/answer")
async def answer(request: Request):
    data = await request.json()
    user_answer = data.get("answer", "")
    q_index = int(data.get("q_index", 0))
    role = data.get("role", "").strip().lower()
    mode = data.get("mode", "").strip().lower()
    questions = QUESTIONS.get(role, {}).get(mode, [])
    if not questions or q_index >= len(questions):
        return {"feedback": "No more questions.", "next_question": None}
    question = questions[q_index]

    prompt = f"""
You are a senior interviewer evaluating a candidate’s response for the role of "{role}" in a {mode} interview.

Question: {question}

Candidate's Answer: {user_answer}

Please analyze the answer thoroughly and provide constructive feedback focusing on:
- Clarity and communication
- Completeness and correctness
- Use of real-world examples or reasoning
- Any potential improvements

Conclude with an overall score from 0 to 10 on a separate line, formatted exactly as:
Score: X
"""

    raw_response = ask_llama(prompt)

    lines = raw_response.splitlines()
    score = 0
    for line in reversed(lines):
        if line.lower().startswith("score:"):
            match = re.search(r"(\d+)", line)
            if match:
                score = int(match.group(1))
            break

    feedback_lines = [l for l in lines if not l.lower().startswith("score:")]
    feedback = "\n".join(feedback_lines).strip() or "No feedback provided."

    next_question = questions[q_index + 1] if q_index + 1 < len(questions) else None

    return {
        "feedback": f"{feedback}\n\nScore: {score}/10",
        "next_question": next_question
    }