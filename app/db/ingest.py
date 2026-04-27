import json
import chromadb
from pathlib import Path

current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent

chroma_path = project_root/"chroma_db"

client = chromadb.PersistentClient(path=chroma_path)

# ✅ RESET COLLECTION
try:
    client.delete_collection("departments")
except:
    pass

collection = client.get_or_create_collection(name="departments")


# ================================
# LOAD DATA
# ================================

with open("departments_cleaned.json", encoding="utf-8") as f:
    dept_data = json.load(f)

with open("doctors_data.json", encoding="utf-8") as f:
    doctor_data = json.load(f)


# ================================
# CHUNK FUNCTION
# ================================

def chunk_text(text, size=120):
    words = text.split()
    return [" ".join(words[i:i+size]) for i in range(0, len(words), size)]


# ================================
# 🔹 STEP 1: DEPARTMENTS
# ================================

for i, dept in enumerate(dept_data["departments"]):

    text = f"""
Department: {dept['name']}

Description:
{dept['description']}

Doctors:
{", ".join(dept.get("doctors", []))}
""".strip()

    chunks = chunk_text(text)

    for j, chunk in enumerate(chunks):

        chunk = chunk.strip()
        if not chunk:
            continue

        chunk_with_context = f"{dept['name']}:\n{chunk}".strip()

        collection.add(
            documents=[chunk_with_context],
            metadatas=[{
                "type": "department",
                "name": dept["name"],
                "doctors": ", ".join(dept.get("doctors", [])),
                "chunk_id": j
            }],
            ids=[f"dept_{i}_{j}"]
        )


# ================================
# 🔹 STEP 2: DOCTORS (NEW)
# ================================

for i, doc in enumerate(doctor_data["doctors"]):

    name = doc.get("name", "")
    position = doc.get("position", "")
    qualification = doc.get("qualification", "")

    # ---------- CHUNK 1: BASIC ----------
    text1 = f"""
Doctor: {name}

Position: {position}
Qualification: {qualification}

Areas of Interest:
{", ".join(doc.get("areas_of_interest", []))}
""".strip()

    collection.add(
        documents=[text1],
        metadatas=[{
            "type": "doctor",
            "name": name,
            "department": position,
            "section": "basic"
        }],
        ids=[f"doc_{i}_basic"]
    )

    # ---------- CHUNK 2: EXPERIENCE ----------
    exp_text = " ".join(doc.get("work_experience", [])[:5])

    if exp_text:
        text2 = f"""
Doctor: {name}

Work Experience:
{exp_text}
""".strip()

        collection.add(
            documents=[text2],
            metadatas=[{
                "type": "doctor",
                "name": name,
                "department": position,
                "section": "experience"
            }],
            ids=[f"doc_{i}_exp"]
        )

    # ---------- CHUNK 3: EDUCATION ----------
    edu_text = " ".join(doc.get("education_training", [])[:3])

    if edu_text:
        text3 = f"""
Doctor: {name}

Education:
{edu_text}
""".strip()

        collection.add(
            documents=[text3],
            metadatas=[{
                "type": "doctor",
                "name": name,
                "department": position,
                "section": "education"
            }],
            ids=[f"doc_{i}_edu"]
        )


print("✅ Departments + Doctors ingested successfully")