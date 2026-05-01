import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

URL = "https://www.balcomedicalcentre.com/facilities"

options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

driver.get(URL)
time.sleep(3)

# ✅ CORRECT TABS SELECTOR
tabs = driver.find_elements(By.XPATH, "//ul[contains(@class,'nav-tabs')]//a")

print(f"Found {len(tabs)} tabs")

facilities = []

for i in range(len(tabs)):
    try:
        # re-fetch tabs (important after DOM update)
        tabs = driver.find_elements(By.XPATH, "//ul[contains(@class,'nav-tabs')]//a")

        tab = tabs[i]
        tab_name = tab.text.strip()

        print(f"\n👉 Clicking: {tab_name}")

        # click tab
        driver.execute_script("arguments[0].click();", tab)
        time.sleep(2)

        # ✅ active tab content (IMPORTANT)
        active_tab = driver.find_element(By.CSS_SELECTOR, ".tab-pane.active")

        boxes = active_tab.find_elements(By.CLASS_NAME, "facilityTab-box")

        for box in boxes:
            try:
                name = box.find_element(By.TAG_NAME, "h3").text.strip()
                img = box.find_element(By.TAG_NAME, "img").get_attribute("src")
                desc = box.find_element(By.TAG_NAME, "p").text.strip()

                facilities.append({
                    "category": tab_name,
                    "name": name,
                    "image": img,
                    "description": desc
                })

                print(f"   ✅ {name}")

            except Exception as e:
                print(f"   ❌ Box error: {e}")

    except Exception as e:
        print(f"❌ Tab error: {e}")


# SAVE
with open("facilities.json", "w", encoding="utf-8") as f:
    json.dump({"facilities": facilities}, f, indent=2, ensure_ascii=False)

print("\n🎉 Done!")

driver.quit()