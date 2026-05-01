from fastapi import FastAPI
import json
import chromadb
from groq import Groq
import os
from pathlib import Path

from dotenv import load_dotenv

current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent

load_dotenv(project_root/".env")

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

data_path = project_root/"data"/"processed"/"departments_cleaned.json"
doctor_data_path = project_root/"data"/"processed"/"doctors_data.json"

# load data (only for listing departments)
facility_data_path = project_root/"data"/"processed"/"facilities_cleaned.json"
with open(data_path, encoding="utf-8") as f:
    data = json.load(f)
with open(doctor_data_path, encoding="utf-8") as f:
    doctor_data = json.load(f)
with open(facility_data_path, encoding="utf-8") as f:
    facility_data = json.load(f)

about_data_path = project_root/"data"/"processed"/"about.json"

with open(about_data_path, encoding="utf-8") as f:
    about_data = json.load(f)

daycare_data_path = project_root/"data"/"processed"/"daycare.json"
health_library_path = project_root/"data"/"processed"/"health_library_cleaned.json"

with open(daycare_data_path, encoding="utf-8") as f:
    daycare_data = json.load(f)

with open(health_library_path, encoding="utf-8") as f:
    health_library_data = json.load(f)

# ✅ connect to Chroma DB
chroma_path = project_root/"chroma_db"
client = chromadb.PersistentClient(path=chroma_path)
collection = client.get_or_create_collection(name="departments")


def get_cache_key(q):
    return " ".join(q.lower().strip().split())


# ✅ LLM function (improved prompt)
def ask_llm(context, question):
    prompt = f"""
You are a helpful assistant for a hospital.

Rules:
- Answer clearly and briefly (max 4-5 lines)
- Use ONLY the provided context
- If multiple doctors match, mention their names clearly
- Do NOT assume anything
- Do NOT hallucinate or invent information
- If answer is not found, say "I don't have that information"


Context:
{context}

Question:
{question}
"""

    try:
        response = client_groq.chat.completions.create(
            model="openai/gpt-oss-120b",  # fast + good
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"LLM Error: {str(e)}"


def retrieve(query, filter_type=None):
    if filter_type:
        return collection.query(
            query_texts=[query],
            n_results=5,
            where={"type": filter_type}
        )
    else:
        return collection.query(
            query_texts=[query],
            n_results=5
        )
    

def rank_doctors(metas, query):
    scores = {}

    for meta in metas:
        if meta.get("type") != "doctor":
            continue

        name = meta.get("name")
        if not name:
            continue

        score = 0

        text = (
            meta.get("department", "") +
            " " +
            meta.get("section", "") +
            " " +
            meta.get("name", "")
        ).lower()

        # 🔹 keyword match boost
        for word in query.split():
            if word in text:
                score += 2

        # 🔹 oncology / cancer boost
        if "cancer" in query and "oncology" in text:
            score += 3

        scores[name] = max(scores.get(name, 0), score)

    # sort
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    return [name for name, _ in ranked[:3]]



doctor_keywords = ["doctor", "doctors", "specialist", "physician", "consultant", "surgeon"]
treatment_keywords = ["treat", "treatment", "cancer", "disease", "therapy"]
list_keywords = ["list", "who are", "show", "all"]
best_keywords = ["best", "top", "recommended", "good"]
facility_keywords = ["room", "facility", "facilities", "ward", "cafeteria", "services"]
about_keywords = ["about", "hospital", "mission", "vision", "contact", "address", "location", "timings"]
daycare_keywords = ["daycare", "chemotherapy", "chemo", "infusion"]
health_keywords = ["health", "article", "library", "symptoms", "prevention", "disease info"]

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

    matched_doctor_name = None

    for doc in doctor_data["doctors"]:
        if doc["name"].lower() in q_lower:
            matched_doctor_name = doc["name"]
            break

# 🔥 Doctor name boosting (for partial matches)
    for doc in doctor_data["doctors"]:
        name_lower = doc["name"].lower()

        if any(part in q_lower for part in name_lower.split()):
            boosted_query += " " + doc["name"]
            break


    # 🔥 Facility name boosting (direct and partial matches)
    for fac in facility_data.get("facilities", []):
        fname = fac.get("name", "").lower()
        if fname and fname in q_lower:
            boosted_query += " " + fac.get("name", "")
            break

    for fac in facility_data.get("facilities", []):
        name_lower = fac.get("name", "").lower()
        if any(part in q_lower for part in name_lower.split()):
            boosted_query += " " + fac.get("name", "")
            break


    # ✅ INTENT 1: list departments
    if any(x in q_lower for x in ["list departments", "all departments", "what departments"]):
        names = [d["name"] for d in data["departments"]]

        response = {"response": ", ".join(names)}
        cache[key] = response

        if len(cache) > CACHE_LIMIT:
            cache.popitem(last=False)

        return response


    is_doctor_query = any(x in q_lower for x in doctor_keywords)
    is_treatment_query = any(x in q_lower for x in treatment_keywords)
    is_list_query = any(x in q_lower for x in list_keywords)
    is_best_query = any(x in q_lower for x in best_keywords) and is_doctor_query
    is_facility_query = any(x in q_lower for x in facility_keywords)
    is_about_query = any(x in q_lower for x in about_keywords) and not is_doctor_query
    is_daycare_query = any(x in q_lower for x in daycare_keywords)
    is_health_query = any(x in q_lower for x in health_keywords)

    # ✅ STEP: semantic retrieval (top 3)
    # 🔹 Additional boosting for daycare and health library
    if is_daycare_query:
        boosted_query += " BMC Cancer Daycare chemotherapy treatment"

    for article in health_library_data.get("articles", []):
        title = article.get("title", "").lower()
        if title and any(word in q_lower for word in title.split() if len(word) > 3):
            boosted_query += " " + article.get("title", "")
            break

    # 🔥 DIRECT NAME MATCH (highest priority)
    if matched_doctor_name:
        results = retrieve(matched_doctor_name, filter_type="doctor")
    elif is_best_query:
        results = retrieve(boosted_query, filter_type="doctor")
    elif is_doctor_query or is_treatment_query:
        results = retrieve(boosted_query, filter_type="doctor")
    elif is_daycare_query:
        results = retrieve(boosted_query, filter_type="daycare")
    elif is_health_query:
        results = retrieve(boosted_query, filter_type="health_library")
    elif is_facility_query:
        results = retrieve(boosted_query, filter_type="facility")
    elif is_about_query:
        results = retrieve(boosted_query, filter_type="about")
    else:
        results = retrieve(boosted_query)


    distances = results.get("distances", [[]])[0]


    if not distances or min(distances) > 1.7:

        # 🔥 fallback to general search (no filter)
        fallback_results = retrieve(q_context)

        # try to extract docs/metas from fallback
        fallback_docs = fallback_results.get("documents", [[]])[0] if fallback_results else []
        fallback_metas = fallback_results.get("metadatas", [[]])[0] if fallback_results else []

        # If fallback also yields nothing, return a helpful message
        if not fallback_docs:
            response = {
                "response": "I couldn’t find exact info. You can ask about doctors, departments, treatments, or hospital details."
            }
            cache[key] = response

            if len(cache) > CACHE_LIMIT:
                cache.popitem(last=False)

            return response

        # otherwise use fallback results and continue processing
        results = fallback_results
        docs = fallback_docs
        metas = fallback_metas

    
    


    # ensure docs/metas are set (may have been set by fallback above)
    if 'docs' not in locals():
        docs = results["documents"][0]
        metas = results["metadatas"][0]

    if is_best_query:

        ranked = rank_doctors(metas, q_lower)

        if ranked:
            response = {
                "response": "Top relevant doctors:\n" +
                "\n".join([f"- {name}" for name in ranked])
            }

            cache[key] = response
            if len(cache) > CACHE_LIMIT:
                cache.popitem(last=False)

            return response

    # combine context
    context = ""

    for d in docs:
        if len(context) < 1500:
            context += d + "\n\n"

    # ✅ INTENT 2: doctor query
    if is_doctor_query:

        # 👉 CASE 1: list-type queries
        if is_list_query:
            answers = []

            for meta in metas:
                if meta.get("type") == "doctor" and meta.get("name"):
                    answers.append(meta["name"])

            unique_answers = list(dict.fromkeys(answers))

            if unique_answers:
                response = {
                    "response": "Relevant doctors:\n" + "\n".join(unique_answers)
                }
                cache[key] = response
                if len(cache) > CACHE_LIMIT:
                    cache.popitem(last=False)

                return response

        # 👉 CASE 2: informational queries → use LLM
        answer = ask_llm(context, q)

        response = {"response": answer}
        cache[key] = response
        if len(cache) > CACHE_LIMIT:
            cache.popitem(last=False)

        return response
    # ✅ INTENT 3a: Daycare query (use LLM with retrieved context)
    if is_daycare_query:

        answer = ask_llm(context, q)

        response = {"response": answer}
        cache[key] = response

        if len(cache) > CACHE_LIMIT:
            cache.popitem(last=False)

        return response

    # ✅ INTENT 3b: Health library query (use LLM with retrieved context)
    if is_health_query:

        answer = ask_llm(context, q)

        response = {"response": answer}
        cache[key] = response

        if len(cache) > CACHE_LIMIT:
            cache.popitem(last=False)

        return response

    # ✅ INTENT 3: LLM answer
    answer = ask_llm(context, q)

    response = {
        "response": answer,
        "matched_departments": [
            m.get("name")
            for m in metas
            if m.get("name")
        ],
        "matched_sources": [
            m.get("name") or m.get("title") or m.get("section") or m.get("type")
            for m in metas
        ]
    }
    cache[key] = response

    if len(cache) > CACHE_LIMIT:
        cache.popitem(last=False)

    return response