from fastapi import FastAPI
import json
from rapidfuzz import fuzz
import requests

app = FastAPI()

with open("departments_cleaned.json", encoding="utf-8") as f:
    data = json.load(f)


# ✅ LLM function
def ask_llm(context, question):
    prompt = f"""
You are a hospital assistant.
Answer ONLY using the given context.
If the answer is not present, say "I don't have that information."

Context:
{context}

Question:
{question}
"""

    try:
        res = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3",
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.3}
            }
        )
        return res.json()["response"]

    except Exception as e:
        return f"LLM Error: {str(e)}"


@app.get("/chat")
def chat(q: str):
    q_lower = q.lower()

    # ✅ INTENT 1: list departments (FIXED)
    if any(x in q_lower for x in ["list departments", "all departments", "what departments"]):
        names = [d["name"] for d in data["departments"]]
        return {"response": ", ".join(names)}

    best_match = None
    best_score = 0

    # ✅ fuzzy matching
    for dept in data["departments"]:
        name = dept["name"].lower()
        score = fuzz.partial_ratio(q_lower, name)

        if score > best_score:
            best_score = score
            best_match = dept

    if best_match and best_score > 50:

        # ✅ INTENT 2: doctor query
        if any(word in q_lower for word in ["doctor", "doctors"]):
            doctors = best_match.get("doctors", [])

            if doctors:
                return {
                    "response": f"Doctors in {best_match['name']}: " + ", ".join(doctors),
                    "matched_department": best_match["name"],
                    "confidence": best_score
                }
            else:
                return {"response": "No doctor data available."}

        # ✅ INTENT 3: normal question → LLM
        answer = ask_llm(best_match["description"], q)

        return {
            "response": answer,
            "matched_department": best_match["name"],
            "confidence": best_score
        }

    return {"response": "Sorry, I couldn't find that info."}