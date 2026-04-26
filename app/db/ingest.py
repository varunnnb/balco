import json
import chromadb

client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(name="departments")

with open("departments_cleaned.json", encoding="utf-8") as f:
    data = json.load(f)

try:
    client.delete_collection("departments")
except:
    pass

collection = client.get_or_create_collection(name="departments")# clear old data


def chunk_text(text, size=120):
    words = text.split()
    return [" ".join(words[i:i+size]) for i in range(0, len(words), size)]

for i, dept in enumerate(data["departments"]):
    
    text = f"""
    Department: {dept['name']}

    Description:
    {dept['description']}

    Doctors:
    {", ".join(dept.get("doctors", []))}
    """.strip()

    chunks = chunk_text(text)

    for j, chunk in enumerate(chunks):

        chunk=chunk.strip()

        if not chunk:
            continue
        
        # add department name to each chunk (important)
        chunk_with_context = f"{dept['name']}:\n{chunk}".strip()

        collection.add(
            documents=[chunk_with_context],
            metadatas=[{
                "name": dept["name"],
                "doctors": ", ".join(dept.get("doctors", [])),
                "chunk_id": j
            }],
            ids=[f"{i}_{j}"]
        )

print("✅ Data ingested successfully")