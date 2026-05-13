#Washington University in St. Louis (Olin School of Business) __WORKING__

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import pandas as pd
import time

# Set up Selenium options
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run in headless mode
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# Path to your ChromeDriver
chrome_driver_path = "/usr/local/bin/chromedriver"  # Update this if needed

# Initialize WebDriver
service = Service(chrome_driver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)

# Open the faculty directory page
url = "https://olin.wustl.edu/faculty-and-research/faculty-directory/index.php?search=&area=Supply%20Chain%20Operations%20%26%20Technology&type=&pageindex=1&pagesize=10"
driver.get(url)

# Allow time for the page to load
time.sleep(5)

# Scrape faculty names and titles
faculty_list = []
faculty_elements = driver.find_elements(By.CLASS_NAME, "card-faculty__content")

for faculty in faculty_elements:
    try:
        name = faculty.find_element(By.CLASS_NAME, "card-faculty__heading").text.strip()
        title = faculty.find_element(By.CLASS_NAME, "card-faculty__copy").text.strip()
        faculty_list.append({"Name": name, "Title": title})
    except:
        continue

# Close the driver
driver.quit()

# Convert to DataFrame
df = pd.DataFrame(faculty_list)

# Save to Excel
df.to_excel("olin_faculty_data.xlsx", index=False)

print("Scraping complete. Data saved as 'olin_faculty_data.xlsx'.")