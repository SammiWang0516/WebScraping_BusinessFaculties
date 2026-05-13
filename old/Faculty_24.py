#University of Maryland at College Park (Robert H. Smith School of Business) __WORKING__

import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# Path to ChromeDriver (Update if needed)
chrome_driver_path = "/usr/local/bin/chromedriver"

# Set up Chrome WebDriver with options
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run without opening browser
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

service = Service(chrome_driver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)

# Open the faculty page
url = "https://www.rhsmith.umd.edu/departments/marketing/faculty?page=2"
driver.get(url)

time.sleep(5)

# Find all faculty members in the directory
faculty_list = driver.find_elements(By.CSS_SELECTOR, "div.col-12.mb-4")

# Store faculty data
faculty_data = []

for faculty in faculty_list:
    try:
        # Extract name
        name_element = faculty.find_element(By.CSS_SELECTOR, "p.person-name a")
        name = name_element.text.strip()

        # Extract titles (Some faculty have multiple titles)
        title_elements = faculty.find_elements(By.CSS_SELECTOR, "ul li")
        titles = [t.text.strip() for t in title_elements if t.text.strip()]

        # Save each title in a separate row
        for title in titles:
            faculty_data.append([name, title])
    
    except Exception as e:
        print(f"Error processing faculty: {e}")
        continue

driver.quit()

csv_filename = "umd_smith_faculty.csv"
df = pd.DataFrame(faculty_data, columns=["Name", "Title"])
df.to_csv(csv_filename, index=False)

print(f"Data successfully saved to {csv_filename}")