#Columbia is done manually. The code didn't work due to their structure. __WORKED__


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

# Open Columbia Business School Accounting Faculty Directory
url = "https://business.columbia.edu/directory/departments/accounting"
driver.get(url)
time.sleep(5)  # Allow page to load

# Function to scrape faculty data
def scrape_faculty():
    faculty_data = []
    
    # Locate all faculty members
    faculty_list = driver.find_elements(By.CSS_SELECTOR, "div.m-listing-faculty")

    for faculty in faculty_list:
        try:
            # Extract faculty name
            name_element = faculty.find_element(By.CSS_SELECTOR, "h3.m-listing-faculty__title")
            name = name_element.text.strip()

            # Extract titles and combine into a single string
            title_elements = faculty.find_elements(By.CSS_SELECTOR, "dt.m-detail-meta__item-title")
            titles = ", ".join([title.text.strip() for title in title_elements if title.text.strip()])

            # Store the faculty data
            faculty_data.append([name, titles])

        except Exception as e:
            print(f"❌ Error processing faculty: {e}")
            continue

    return faculty_data

# Scrape faculty data
faculty_data = scrape_faculty()

# Close the browser
driver.quit()

# Save to CSV
csv_filename = "columbia_business_faculty.csv"
df = pd.DataFrame(faculty_data, columns=["Name", "Title"])
df.to_csv(csv_filename, index=False)

print(f"✅ Successfully scraped {len(faculty_data)} faculty members and saved to {csv_filename}")