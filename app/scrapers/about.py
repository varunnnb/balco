import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json

BASE_URL = "https://www.balcomedicalcentre.com"
URL = BASE_URL + "/about"

headers = {
    "User-Agent": "Mozilla/5.0"
}


def clean_text(tag):
    if not tag:
        return ""
    return tag.get_text(separator=" ", strip=True)


def scrape_about():
    res = requests.get(URL, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")

    data = {}

    # =====================================
    # 1. INTRO / ABOUT
    # =====================================
    about_div = soup.find("div", class_="abt-wel-txt")

    if about_div:
        data["about"] = {
            "title": clean_text(about_div.find("h1")),
            "subtitle": clean_text(about_div.find("h3")),
            "description": clean_text(about_div.find("p"))
        }

    # =====================================
    # 2. MISSION / VISION / VALUES
    # =====================================
    mvv = []

    boxes = soup.find_all("div", class_="miss-viss-bx")

    for box in boxes:
        img = box.find("img")
        title = img["src"].split("/")[-1].split(".")[0] if img else ""

        content = clean_text(box)

        mvv.append({
            "type": title,  # mission / vision / values
            "content": content
        })

    data["mission_vision_values"] = mvv

    # =====================================
    # 3. LEADERS
    # =====================================
    leaders = []

    leader_sections = soup.find_all("div", class_="leader-content")

    for section in leader_sections:
        try:
            name = clean_text(section.find("h2"))
            role = clean_text(section.find("h3"))

            # combine all paragraphs
            desc = " ".join([p.get_text(strip=True) for p in section.find_all("p")])

            # find image (previous or next sibling)
            parent = section.parent
            img_tag = parent.find_previous("img") or parent.find_next("img")

            image = ""
            if img_tag and img_tag.get("src"):
                image = urljoin(BASE_URL, img_tag["src"])

            # social links
            social_links = []
            ul = parent.find_previous("ul") or parent.find_next("ul")

            if ul:
                for a in ul.find_all("a"):
                    href = a.get("href")
                    if href:
                        social_links.append(href)

            leaders.append({
                "name": name,
                "role": role,
                "description": desc,
                "image": image,
                "social_links": social_links
            })

            print(f"✅ Leader: {name}")

        except Exception as e:
            print(f"❌ Leader error: {e}")

    data["leaders"] = leaders

    # =====================================
    # 4. CONTACT DETAILS
    # =====================================
    contacts = {
        "phones": [],
        "emails": [],
        "timings": []
    }

    contact_ul = soup.find("ul", class_="deatils-contact")

    if contact_ul:
        for li in contact_ul.find_all("li"):

            text = clean_text(li)

            a_tag = li.find("a")

            if a_tag:
                href = a_tag.get("href", "")

                if "tel:" in href:
                    contacts["phones"].append(text)

                elif "mailto:" in href:
                    contacts["emails"].append(text)

            else:
                # timings
                if text:
                    contacts["timings"].append(text)

    data["contacts"] = contacts

    # =====================================
    # 5. SOCIAL MEDIA
    # =====================================
    social_links = []

    social_div = soup.find("ul", class_="socialMedia")

    if social_div:
        for a in social_div.find_all("a"):
            href = a.get("href")
            if href:
                social_links.append(href)

    data["social_media"] = social_links

    # =====================================
    # 6. ADDRESS
    # =====================================
    address_div = soup.find("div", class_="footer-col-content footpadd-left-60")

    if address_div:
        address = clean_text(address_div.find("p"))
        data["address"] = address

    return data


def main():
    data = scrape_about()

    with open("about.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("🎉 Done! Saved to about.json")


if __name__ == "__main__":
    main()