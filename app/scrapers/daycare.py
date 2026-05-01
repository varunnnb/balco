import requests
from bs4 import BeautifulSoup
import json

URL = "https://www.balcomedicalcentre.com/BMC-City-Daycare"

headers = {
    "User-Agent": "Mozilla/5.0"
}


def clean_text(tag):
    if not tag:
        return ""
    return tag.get_text(separator=" ", strip=True)


def scrape_daycare():
    res = requests.get(URL, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")

    data = {}

    # =========================================
    # 1. OVERVIEW
    # =========================================
    overview_div = soup.find("div", class_="section-title")

    overview_text = []
    if overview_div:
        paragraphs = overview_div.find_all("p")
        for p in paragraphs:
            text = clean_text(p)
            if text:
                overview_text.append(text)

    data["overview"] = " ".join(overview_text)

    # =========================================
    # 2. SERVICES OFFERED
    # =========================================
    services = []

    service_section = soup.find("section", id="services-offered-focus")

    if service_section:
        items = service_section.find_all("h4")

        for item in items:
            text = clean_text(item)
            if text:
                services.append(text)

    data["services"] = list(dict.fromkeys(services))  # remove duplicates

    # =========================================
    # 3. BOOK APPOINTMENT
    # =========================================
    booking = {}

    booking_div = soup.find("div", class_="book-appointment-center")

    if booking_div:
        text = clean_text(booking_div.find("p"))

        # extract phone from text
        phones = []
        for a in booking_div.find_all("a"):
            href = a.get("href", "")
            if "tel:" in href:
                phones.append(href.replace("tel:", ""))

        booking = {
            "info": text,
            "phones": phones
        }

    data["booking"] = booking

    # =========================================
    # 4. WHY VISIT (CAROUSEL - REMOVE DUPLICATES)
    # =========================================
    why_visit = []
    seen = set()

    carousel = soup.find("section", id="bmc-hospital-focus")

    if carousel:
        items = carousel.find_all("div", class_="item")

        for item in items:
            title_tag = item.find("h4")
            desc_tag = item.find("p")

            title = clean_text(title_tag)
            desc = clean_text(desc_tag)

            key = (title, desc)

            if title and key not in seen:
                seen.add(key)

                why_visit.append({
                    "title": title,
                    "description": desc
                })

    data["why_visit"] = why_visit

    # =========================================
    # 5. FAQ
    # =========================================
    faqs = []

    faq_section = soup.find("section", id="faq-focus")

    if faq_section:
        panels = faq_section.find_all("div", class_="panel")

        for panel in panels:
            try:
                question_tag = panel.find("a")
                answer_tag = panel.find("div", class_="panel-body")

                question = clean_text(question_tag)
                answer = clean_text(answer_tag)

                if question and answer:
                    faqs.append({
                        "question": question,
                        "answer": answer
                    })

            except:
                continue

    data["faq"] = faqs

    return data


def main():
    data = scrape_daycare()

    with open("daycare.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("✅ Done! Saved to daycare.json")


if __name__ == "__main__":
    main()