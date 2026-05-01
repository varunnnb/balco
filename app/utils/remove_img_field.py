import json

INPUT_FILE = "facilities.json"
OUTPUT_FILE = "facilities_cleaned.json"

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

for facility in data.get("facilities", []):
    facility.pop("image", None)  # safely remove if exists

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("✅ Cleaned file saved as facilities_cleaned.json")