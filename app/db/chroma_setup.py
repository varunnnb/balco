import json
import chromadb

# load your data
with open("departments_cleaned.json", encoding="utf-8") as f:
    data = json.load(f)

# create persistent DB
client = chromadb.PersistentClient(path="./chroma_db")

collection = client.get_or_create_collection(name="departments")

# clear old data (optional but recommended first time)
client.delete_collection("departments")
collection = client.get_or_create_collection(name="departments")

for i, dept in enumerate(data["departments"]):
    text = f"""
Department: {dept['name']}

Description:
{dept['description']}

Doctors:
{", ".join(dept.get("doctors", []))}
"""

    collection.add(
        documents=[text],
        metadatas=[{
            "name": dept["name"],
            "doctors": ", ".join(dept.get("doctors", []))
        }],
        ids=[str(i)]
    )

print("Chroma DB created!")