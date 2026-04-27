import time
import json
import requests
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


BASE_URL = "https://www.balcomedicalcentre.com"
LIST_URL = f"{BASE_URL}/doctors"

headers = {
    "User-Agent": "Mozilla/5.0"
}


# ✅ Setup Selenium
def setup_driver():
    options = Options()
    options.add_argument("--headless")  # remove if you want to see browser
    options.add_argument("--disable-blink-features=AutomationControlled")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    return driver


# ✅ Get doctor links (JS rendered)
def get_doctor_links(driver):
    driver.get(LIST_URL)
    time.sleep(5)  # wait for JS to load

    soup = BeautifulSoup(driver.page_source, "html.parser")

    doctors = []
    seen = set()

    images = soup.find_all("img")

    print(f"Total images found: {len(images)}")

    for img in images:
        src = img.get("src") or img.get("data-src") or ""
        alt = img.get("alt", "").strip()

        if "uploads/doctor" in src and alt:
            slug = src.split("/")[-1].split(".")[0]
            doctor_url = f"{BASE_URL}/doctors/{slug}"

            if doctor_url in seen:
                continue
            seen.add(doctor_url)

            doctors.append({
                "name": alt,
                "url": doctor_url
            })

    return doctors


# ✅ Extract lists
def extract_list(panel):
    if not panel:
        return []

    results = []

    # 1️⃣ Try list items first
    items = panel.find_all("li")
    if items:
        results = [li.get_text(strip=True) for li in items]

    else:
        # 2️⃣ fallback to <p> tags
        paragraphs = panel.find_all("p")

        for p in paragraphs:
            text = p.get_text(strip=True)
            if text:
                results.append(text)

    return results


# ✅ Scrape doctor page
def scrape_doctor_details(doctor):
    try:
        res = requests.get(doctor["url"], headers=headers)
        soup = BeautifulSoup(res.text, "html.parser")

        name_tag = soup.find("h2")
        name = name_tag.get_text(strip=True) if name_tag else doctor["name"]

        p_tags = soup.select(".profileBanner-txt p")

        position = ""
        qualification = ""

        if len(p_tags) >= 1:
            position = p_tags[0].get_text(strip=True)

        if len(p_tags) >= 2:
            qualification = p_tags[1].get_text(strip=True)

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


# ✅ MAIN
def main():
    driver = setup_driver()

    doctor_links = get_doctor_links(driver)
    print(f"Found {len(doctor_links)} doctors")

    all_data = []

    for doc in doctor_links:
        print(f"Scraping: {doc['name']}")
        data = scrape_doctor_details(doc)

        if data:
            all_data.append(data)

        time.sleep(1)

    driver.quit()

    with open("doctors_data.json", "w", encoding="utf-8") as f:
        json.dump({"doctors": all_data}, f, indent=2, ensure_ascii=False)

    print("✅ Done!")


if __name__ == "__main__":
    main()