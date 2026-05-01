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


dept_data_path = project_root/"data"/"processed"/"departments_cleaned.json"
doctor_data_path = project_root/"data"/"processed"/"doctors_data.json"
daycare_data_path = project_root/"data"/"processed"/"daycare.json"
health_library_path = project_root/"data"/"processed"/"health_library_cleaned.json"
facility_data_path = project_root/"data"/"processed"/"facilities_cleaned.json"
about_data_path = project_root/"data"/"processed"/"about.json"

with open(dept_data_path, encoding="utf-8") as f:
    dept_data = json.load(f)
with open(doctor_data_path, encoding="utf-8") as f:
    doctor_data = json.load(f)
with open(facility_data_path, encoding="utf-8") as f:
    facilities_data = json.load(f)
with open(about_data_path, encoding="utf-8") as f:
    about_data = json.load(f)
with open(daycare_data_path, encoding="utf-8") as f:
    daycare_data = json.load(f)
with open(health_library_path, encoding="utf-8") as f:
    health_library_data = json.load(f)


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


# ================================
# 🔹 STEP 3: ABOUT
# ================================

about = about_data.get("about", {})

# ---------- OVERVIEW ----------
overview = about.get("description", "")
if overview and overview.strip():
    text = f"""
About BALCO Medical Centre:
{overview}
""".strip()

    collection.add(
        documents=[text],
        metadatas=[{
            "type": "about",
            "section": "overview"
        }],
        ids=["about_overview"]
    )

# ---------- MISSION / VISION / VALUES ----------
for i, item in enumerate(about_data.get("mission_vision_values", [])):
    content = item.get("content", "")
    if not content or not content.strip():
        continue

    text = f"""
{item.get("type", "").title()}:
{content}
""".strip()

    collection.add(
        documents=[text],
        metadatas=[{
            "type": "about",
            "section": item.get("type", "")
        }],
        ids=[f"about_{item.get('type','item')}_{i}"]
    )

# ---------- CONTACT DETAILS ----------
contacts = about_data.get("contacts", {})
phones = contacts.get("phones", [])
emails = contacts.get("emails", [])
timings = contacts.get("timings", [])
address = about_data.get("address", "")

if phones or emails or timings or (isinstance(address, str) and address.strip()):
    text = f"""
Contact Details:
Phones: {", ".join(phones)}
Emails: {", ".join(emails)}

Hospital Timings:
OPD Timings: {", ".join(timings)}

Outpatient Department (OPD) Hours:
{", ".join(timings)}

Opening Hours:
{", ".join(timings)}

Clinic Timings:
{", ".join(timings)}

Visiting Hours:
{", ".join(timings)}

Address: {address}
""".strip()

    if text.strip():
        collection.add(
            documents=[text],
            metadatas=[{
                "type": "about",
                "section": "contact"
            }],
            ids=["about_contact"]
        )


# ================================
# 🔹 STEP 4: FACILITIES
# ================================

for i, facility in enumerate(facilities_data.get("facilities", [])):
    desc = facility.get("description", "")
    if not desc or not desc.strip():
        continue

    text = f"""
Facility: {facility.get("name", "")}

Category: {facility.get("category", "")}

Description:
{desc}
""".strip()

    collection.add(
        documents=[text],
        metadatas=[{
            "type": "facility",
            "name": facility.get("name", ""),
            "category": facility.get("category", "")
        }],
        ids=[f"facility_{i}"]
    )

# ================================
# 🔹 STEP 5: DAYCARE
# ================================

overview = daycare_data.get("overview", "")

if overview and isinstance(overview, str) and overview.strip():
    text = f"""
BMC Cancer Daycare Overview:
{overview}
""".strip()

    collection.add(
        documents=[text],
        metadatas=[{
            "type": "daycare",
            "section": "overview"
        }],
        ids=["daycare_overview"]
    )

for i, service in enumerate(daycare_data.get("services", [])):
    if not service or not str(service).strip():
        continue

    text = f"""
Daycare Service:
{service}
""".strip()

    collection.add(
        documents=[text],
        metadatas=[{
            "type": "daycare",
            "section": "service"
        }],
        ids=[f"daycare_service_{i}"]
    )

booking = daycare_data.get("booking", {})
info = booking.get("info", "")
phones = booking.get("phones", [])

if (info and str(info).strip()) or phones:
    text = f"""
Daycare Booking Information:
{info}

Phone: {", ".join(phones)}
""".strip()

    collection.add(
        documents=[text],
        metadatas=[{
            "type": "daycare",
            "section": "booking"
        }],
        ids=["daycare_booking"]
    )

for i, item in enumerate(daycare_data.get("why_visit", [])):
    title = item.get("title", "")
    desc = item.get("description", "")
    if not (title or desc):
        continue

    text = f"""
{title}:
{desc}
""".strip()

    collection.add(
        documents=[text],
        metadatas=[{
            "type": "daycare",
            "section": "why_visit"
        }],
        ids=[f"daycare_why_{i}"]
    )

for i, faq in enumerate(daycare_data.get("faq", [])):
    q = faq.get("question", "")
    a = faq.get("answer", "")
    if not (q or a):
        continue

    text = f"""
Question: {q}
Answer: {a}
""".strip()

    collection.add(
        documents=[text],
        metadatas=[{
            "type": "daycare",
            "section": "faq"
        }],
        ids=[f"daycare_faq_{i}"]
    )


# ================================
# 🔹 STEP 6: HEALTH LIBRARY
# ================================

for i, article in enumerate(health_library_data.get("articles", [])):
    title = article.get("title", "")
    content = article.get("content", "") or article.get("description", "")

    if not content:
        continue

    text = f"""
Health Article: {title}

{content}
""".strip()

    chunks = chunk_text(text)

    for j, chunk in enumerate(chunks):
        collection.add(
            documents=[chunk.strip()],
            metadatas=[{
                "type": "health_library",
                "title": title,
                "chunk_id": j
            }],
            ids=[f"health_{i}_{j}"]
        )

print("✅ Departments + Doctors + About + Facilities + Daycare + Health Library ingested successfully")