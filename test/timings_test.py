import chromadb
from pathlib import Path

db_path = Path("chroma_db")  # adjust path
client = chromadb.PersistentClient(path=str(db_path))
collection = client.get_collection("departments")

query = "hospital timings"

results = collection.query(
    query_texts=[query],
    n_results=10
)

print("\n==== QUERY ====\n", query)

docs = results["documents"][0]
metas = results["metadatas"][0]
distances = results.get("distances", [[]])[0]

for i in range(len(docs)):
    print("\n---------------------------")
    print(f"Result {i+1}")
    print("Distance:", distances[i] if distances else "N/A")
    print("Type:", metas[i].get("type"))
    print("Section:", metas[i].get("section"))
    print("Content:\n", docs[i][:400])