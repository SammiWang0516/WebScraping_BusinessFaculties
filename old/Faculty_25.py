#Ohio State University (Fisher College of Business) __WORKING__


import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

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
url = "https://fisher.osu.edu/directory?first_name=&last_name=&department=224&expertise=All&type=All&page=1"
driver.get(url)

time.sleep(5)

# Find all faculty members
faculty_list = driver.find_elements(By.CSS_SELECTOR, "div.row.person-item")

# Store faculty data
faculty_data = []

for faculty in faculty_list:
    try:
        # Extract first and last name
        first_name = faculty.find_element(By.CSS_SELECTOR, "span.first-name").text.strip()
        last_name = faculty.find_element(By.CSS_SELECTOR, "span.last-name").text.strip()
        full_name = f"{first_name} {last_name}"

        # Extract titles
        title_element = faculty.find_element(By.CSS_SELECTOR, "span.title")
        titles = title_element.text.split(",")  # Split multiple titles

        # Save each title in a separate row
        for title in titles:
            faculty_data.append([full_name, title.strip()])

    except Exception as e:
        print(f"Error processing faculty: {e}")
        continue

driver.quit()

# Save to CSV
csv_filename = "osu_fisher_faculty.csv"
df = pd.DataFrame(faculty_data, columns=["Name", "Title"])
df.to_csv(csv_filename, index=False)

print(f"Data successfully saved to {csv_filename}")