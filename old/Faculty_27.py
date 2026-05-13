#Boston College (Carroll School of Management) _Working__

import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Path to ChromeDriver (update if needed)
chrome_driver_path = "/usr/local/bin/chromedriver"

# Set up Chrome WebDriver with options
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run in headless mode
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

service = Service(chrome_driver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)

# Open the faculty directory page
url = "https://www.bc.edu/bc-web/schools/carroll-school/faculty-research/faculty-expertise.html"
driver.get(url)

# Wait for page to load
time.sleep(5)

#Click the "Accounting" department filter button 
try:
    accounting_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button.tag-filter.Marketing"))
    )
    accounting_button.click()
    print("Clicked on 'Accounting' department filter.")
    time.sleep(5)  # Wait for the page to reload
except Exception as e:
    print(f"Failed to click Accounting filter: {e}")
    driver.quit()
    exit()

#Click "View More" button until all faculty are loaded
while True:
    try:
        view_more_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.loadmore"))
        )
        view_more_button.click()
        print("Clicked 'View More' button to load more faculty...")
        time.sleep(5)  # Wait for content to load
    except:
        print("No more 'View More' button found. All faculty should be loaded.")
        break

#Scrape data
faculty_list = driver.find_elements(By.CSS_SELECTOR, "div.person-list-expertise.row")
data = []

for faculty in faculty_list:
    try:
        # Extract name
        name = faculty.find_element(By.CSS_SELECTOR, "h3 a").text.strip()

        # Extract all titles
        title_elements = faculty.find_elements(By.CSS_SELECTOR, "h4")
        titles = "; ".join([t.text.strip() for t in title_elements if t.text.strip()])  # Keep multiple titles as one value

        # Store faculty data
        data.append([name, titles])

    except Exception as e:
        print(f"Error processing faculty: {e}")
        continue

csv_filename = "boston_college_accounting_faculty.csv"
df = pd.DataFrame(data, columns=["Name", "Title"])
df.to_csv(csv_filename, index=False)

driver.quit()

print(f"Data successfully saved to {csv_filename}")