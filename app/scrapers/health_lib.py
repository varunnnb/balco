import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

BASE_URL = "https://www.balcomedicalcentre.com/health-library"


# ------------------ SETUP DRIVER ------------------
def setup_driver():
    options = Options()
    options.add_argument("--start-maximized")
    # options.add_argument("--headless")  # enable if needed

    driver = webdriver.Chrome(options=options)
    return driver


# ------------------ SCRAPE CURRENT PAGE ------------------
def scrape_articles_from_page(driver):
    articles = []

    time.sleep(2)

    rows = driver.find_elements(By.CSS_SELECTOR, ".list-item")

    for row in rows:
        try:
            # URL
            a = row.find_element(By.TAG_NAME, "a")
            url = a.get_attribute("href")

            # TITLE
            title = row.find_element(By.TAG_NAME, "h4").text.strip()

            # DATE
            date = row.find_element(By.TAG_NAME, "p").text.strip()

            # CATEGORY
            category = row.find_element(By.TAG_NAME, "h5").text.strip()

            # FULL CONTENT (hidden span)
            hidden_span = row.find_element(By.CSS_SELECTOR, "span[style*='display: none']")
            content_html = hidden_span.get_attribute("innerHTML")

            articles.append({
                "title": title,
                "date": date,
                "category": category,
                "content_html": content_html,
                "url": url
            })

        except Exception as e:
            print("⚠️ Skipping one article:", e)
            continue

    return articles


# ------------------ PAGINATION ------------------
def go_to_next_page(driver):
    try:
        next_btn = driver.find_element(By.ID, "test_next")

        # check if disabled
        if "disabled" in next_btn.get_attribute("class"):
            return False

        next_btn.click()
        time.sleep(2)
        return True

    except:
        return False


# ------------------ MAIN ------------------
def main():
    driver = setup_driver()
    driver.get(BASE_URL)

    all_articles = []
    page = 1

    while True:
        print(f"📄 Scraping page {page}...")

        articles = scrape_articles_from_page(driver)
        print(f"   Found {len(articles)} articles")

        all_articles.extend(articles)

        if not go_to_next_page(driver):
            break

        page += 1

    driver.quit()

    # SAVE JSON
    with open("health_library.json", "w", encoding="utf-8") as f:
        json.dump({"articles": all_articles}, f, indent=2, ensure_ascii=False)

    print(f"\n✅ DONE! Total articles scraped: {len(all_articles)}")


if __name__ == "__main__":
    main()