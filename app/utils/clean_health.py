import json
from bs4 import BeautifulSoup

INPUT_FILE = "health_library.json"
OUTPUT_FILE = "health_library_cleaned.json"


def clean_html(html):
    soup = BeautifulSoup(html, "html.parser")

    cleaned = []

    for tag in soup.find_all(["h1", "h2", "h3", "b", "u", "p", "li"]):
        text = tag.get_text(" ", strip=True)

        if not text:
            continue

        if tag.name == "li":
            cleaned.append(f"- {text}")
        else:
            cleaned.append(text)

    return "\n".join(cleaned)


def main():
    with open(INPUT_FILE, encoding="utf-8") as f:
        data = json.load(f)

    cleaned_articles = []

    for article in data["articles"]:
        cleaned_text = clean_html(article["content_html"])

        cleaned_articles.append({
            "title": article["title"],
            "date": article["date"],
            "category": [c.strip() for c in article["category"].split(",")],
            "content": cleaned_text,
            "url": article["url"]
        })

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump({"articles": cleaned_articles}, f, indent=2, ensure_ascii=False)

    print("✅ Cleaned data saved!")


if __name__ == "__main__":
    main()