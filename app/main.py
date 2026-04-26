from fastapi import FastAPI
import json
import chromadb
from groq import Groq
import os

from dotenv import load_dotenv
import os

load_dotenv()

from collections import OrderedDict

CACHE_LIMIT = 100
cache = OrderedDict()

from fastapi.middleware.cors import CORSMiddleware

client_groq = Groq(api_key=os.getenv("GROQ_API_KEY"))

sessions = {}

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all (for dev)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# load data (only for listing departments)
with open("departments_cleaned.json", encoding="utf-8") as f:
    data = json.load(f)

# ✅ connect to Chroma DB
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(name="departments")


def get_cache_key(q):
    return " ".join(q.lower().strip().split())


# ✅ LLM function (improved prompt)
def ask_llm(context, question):
    prompt = f"""
You are a helpful assistant for a hospital.

Rules:
- Answer clearly and briefly
- Use ONLY the provided context
- Do NOT assume anything
- If answer is not found, say "I don't have that information
- Answer in 4-5 lines maximum"

Context:
{context}

Question:
{question}
"""

    try:
        response = client_groq.chat.completions.create(
            model="groq/compound-mini",  # fast + good
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"LLM Error: {str(e)}"


@app.get("/chat")
def chat(q: str, session_id: str = "default"):

    q_lower = q.lower()

    history = sessions.get(session_id, [])

    # add current query
    history.append(q)

    # keep only last 3 messages
    sessions[session_id] = history[-3:]

    q_context = " ".join(history[-2:])

    key = get_cache_key(q_context)
    if key in cache:
        cache.move_to_end(key)
        return cache[key]    

    boosted_query = q_context

    for dept in data["departments"]:
        if dept["name"].lower() in q_context.lower():
            boosted_query += " " + dept["name"]


    # ✅ INTENT 1: list departments
    if any(x in q_lower for x in ["list departments", "all departments", "what departments"]):
        names = [d["name"] for d in data["departments"]]

        response = {"response": ", ".join(names)}
        cache[key] = response

        if len(cache) > CACHE_LIMIT:
            cache.popitem(last=False)

        return response

    # ✅ STEP: semantic retrieval (top 3)
    results = collection.query(
        query_texts=[boosted_query],
        n_results=5
    )

    distances = results.get("distances", [[]])[0]


    if not distances or min(distances) > 1.2:

        response = {
            "response": "I couldn’t find exact info. You can ask about departments, doctors, or treatments."
        }
        cache[key] = response

        if len(cache) > CACHE_LIMIT:
            cache.popitem(last=False)
        return response
    


    docs = results["documents"][0]
    metas = results["metadatas"][0]

    # combine context
    context = "\n\n".join(docs)

    # ✅ INTENT 2: doctor query
    if any(x in q_lower for x in ["doctor", "doctors", "specialist", "physician", "consultant", "surgeon"]):
        answers = []

        for meta in metas:
            doctors = meta.get("doctors")

            if doctors:
                answers.append(f"{meta['name']}: {doctors}")

        # ✅ remove duplicates + keep order
        unique_answers = list(dict.fromkeys(answers))

        if unique_answers:
            response = {"response": "\n\n".join(unique_answers)}
            cache[key] = response
            if len(cache) > CACHE_LIMIT:
                cache.popitem(last=False)

            return response

    # ✅ INTENT 3: LLM answer
    answer = ask_llm(context, q)

    response = {
        "response": answer,
        "matched_departments": [m["name"] for m in metas]
    }
    cache[key] = response

    if len(cache) > CACHE_LIMIT:
        cache.popitem(last=False)

    return response