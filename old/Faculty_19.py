#University of Minnesota at Twin Cities (Carlson School of Management) __WORKING__
#Change the url and the headings. depending on how many heading are on the department website

import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# Path to ChromeDriver (update this if necessary)
chrome_driver_path = "/usr/local/bin/chromedriver"

# Set up Selenium options
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run in headless mode
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# Start WebDriver
service = Service(chrome_driver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)

# Open the faculty page
url = "https://carlsonschool.umn.edu/departments/work-organizations/faculty"
driver.get(url)

# Wait for the page to load
time.sleep(5)

# Store all faculty data
all_data = []

### **Step 1: Scrape the First Expanded Section ("collapse0") Before Clicking Any Buttons**
faculty_list = driver.find_elements(By.CSS_SELECTOR, "div#collapse0 div.staff-faculty__wrapper")
for faculty in faculty_list:
    try:
        name = faculty.find_element(By.CSS_SELECTOR, "a.staff-faculty__item--name span").text.strip()
        titles = faculty.find_elements(By.CSS_SELECTOR, "div.staff-faculty__item--position")

        # Store each title in a separate row
        for title in titles:
            title_text = title.text.strip()
            if title_text:  # Ensure it's not empty
                all_data.append([name, title_text])
    except Exception as e:
        print(f"Skipping faculty entry due to error: {e}")
        continue

print(f"Scraped first expanded section (collapse0)")

### **Step 2: Click Each Dropdown to Expand & Scrape Faculty Data**
heading_ids = ["heading1", "heading2", "heading3"]  # Manually add all headings except "heading0"

for heading_id in heading_ids:
    try:
        dropdown = driver.find_element(By.ID, heading_id)
        driver.execute_script("arguments[0].click();", dropdown)
        time.sleep(3)  # Small delay to allow content to load
        print(f"Clicked {heading_id}")
    except Exception as e:
        print(f"Failed to click {heading_id}: {e}")
        continue

    # Extract faculty data for this dropdown
    faculty_list = driver.find_elements(By.CSS_SELECTOR, f"div#{dropdown.get_attribute('aria-controls')} div.staff-faculty__wrapper")

    for faculty in faculty_list:
        try:
            name = faculty.find_element(By.CSS_SELECTOR, "a.staff-faculty__item--name span").text.strip()
            titles = faculty.find_elements(By.CSS_SELECTOR, "div.staff-faculty__item--position")

            # Store each title in a separate row
            for title in titles:
                title_text = title.text.strip()
                if title_text:  # Ensure it's not empty
                    all_data.append([name, title_text])
        except Exception as e:
            print(f"Skipping faculty entry due to error: {e}")
            continue

# Close the driver
driver.quit()

# Save to CSV (Append mode)
csv_filename = "carlson_faculty_all.csv"
df = pd.DataFrame(all_data, columns=["Name", "Title"])
df.to_csv(csv_filename, index=False)

print(f"Data successfully saved to {csv_filename}")