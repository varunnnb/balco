import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json
import time

BASE_URL = "https://www.balcomedicalcentre.com"
LIST_URL = f"{BASE_URL}/doctors"

headers = {
    "User-Agent": "Mozilla/5.0"
}

def get_doctor_links():
    res = requests.get(LIST_URL, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")

    doctors = []

    images = soup.find_all("img")

    for img in images:
        src = img.get("src", "")
        alt = img.get("alt", "").strip()

        if "/uploads/doctor/" in src and alt:
            # construct doctor profile URL
            slug = src.split("/")[-1].replace(".jpg", "")
            doctor_url = f"{BASE_URL}/doctors/{slug}"

            doctors.append({
                "name": alt,
                "url": doctor_url
            })

    return doctors


def extract_list(panel):
    if not panel:
        return []

    items = panel.find_all("li")
    return [li.get_text(strip=True) for li in items]


def scrape_doctor_details(doctor):
    try:
        res = requests.get(doctor["url"], headers=headers)
        soup = BeautifulSoup(res.text, "html.parser")

        # --- BASIC INFO ---
        name_tag = soup.find("h2")
        name = name_tag.get_text(strip=True) if name_tag else doctor["name"]

        p_tags = soup.select(".profileBanner-txt p")

        position = ""
        qualification = ""

        if len(p_tags) >= 1:
            position = p_tags[0].get_text(strip=True)

        if len(p_tags) >= 2:
            qualification = p_tags[1].get_text(strip=True)

        # --- PANELS ---
        panels = soup.find_all("div", class_="panel")

        education = []
        experience = []
        interests = []

        for panel in panels:
            title = panel.find("a")
            if not title:
                continue

            heading = title.get_text(strip=True).lower()

            body = panel.find("div", class_="panel-body")

            if "education" in heading:
                education = extract_list(body)

            elif "work experience" in heading:
                experience = extract_list(body)

            elif "area of interest" in heading:
                interests = extract_list(body)

        return {
            "name": name,
            "profile_url": doctor["url"],
            "position": position,
            "qualification": qualification,
            "education_training": education,
            "work_experience": experience,
            "areas_of_interest": interests
        }

    except Exception as e:
        print(f"Error scraping {doctor['url']}: {e}")
        return None


def main():
    doctor_links = get_doctor_links()
    print(f"Found {len(doctor_links)} doctors")

    all_data = []

    for doc in doctor_links:
        print(f"Scraping: {doc['name']}")
        data = scrape_doctor_details(doc)

        if data:
            all_data.append(data)

        time.sleep(1)  # be polite

    with open("doctors_data.json", "w", encoding="utf-8") as f:
        json.dump({"doctors": all_data}, f, indent=2, ensure_ascii=False)

    print("✅ Done!")


if __name__ == "__main__":
    main()