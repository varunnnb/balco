import json

INPUT_FILE = "departments.json"
OUTPUT_FILE = "departments_cleaned.json"

def clean_description(desc):
    if "Our Experts" in desc:
        return desc.split("Our Experts")[0].strip()
    return desc  # unchanged

def clean_doctor_name(name):
    if "-" in name:
        return name.replace("-", " ").title()
    return name  # unchanged

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

for dept in data.get("departments", []):
    
    # ✅ Clean description
    if "description" in dept:
        dept["description"] = clean_description(dept["description"])
    
    # ✅ Clean doctor names
    if "doctors" in dept and isinstance(dept["doctors"], list):
        cleaned_doctors = []
        for doc in dept["doctors"]:
            cleaned_doctors.append(clean_doctor_name(doc))
        dept["doctors"] = cleaned_doctors

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("Cleaning complete!")