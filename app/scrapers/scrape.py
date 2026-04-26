import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin

BASE_URL = "https://www.balcomedicalcentre.com"
main_url = f"{BASE_URL}/specialities"

response = requests.get(main_url)
soup = BeautifulSoup(response.text, "html.parser")

departments = []
seen = set()

links = soup.find_all("a")

for link in links:
    href = link.get("href")
    name = link.text.strip()

    if href and "/specialities/" in href and name and not href.endswith("/specialities"):
        dept_url = urljoin(BASE_URL, href)

        if dept_url in seen:
            continue
        seen.add(dept_url)

        print(f"Scraping: {dept_url}")

        try:
            dept_res = requests.get(dept_url)
            dept_soup = BeautifulSoup(dept_res.text, "html.parser")

            # ✅ 1. Extract description
            desc_div = dept_soup.find("div", class_="speciality-tab-contentBx")
            description = desc_div.get_text(separator=" ", strip=True) if desc_div else ""

            # ✅ 2. Extract doctors (from img alt)
            doctors = []
            images = dept_soup.find_all("img")

            for img in images:
                src = img.get("src", "")
                alt = img.get("alt", "").strip()

                if "/uploads/doctor/" in src and alt:
                    doctors.append(alt)

            departments.append({
                "name": name,
                "url": dept_url,
                "description": description,
                "doctors": doctors
            })

        except Exception as e:
            print(f"Error with {dept_url}: {e}")

# SAVE JSON
with open("departments.json", "w", encoding="utf-8") as f:
    json.dump({"departments": departments}, f, indent=2, ensure_ascii=False)

print("Done!")