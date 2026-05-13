#Harvard university __WORKING__


import csv
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# Path to ChromeDriver (Update if needed)
chrome_driver_path = "/usr/local/bin/chromedriver"

# Set up Selenium options
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run in headless mode
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# Start WebDriver
service = Service(chrome_driver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)

# Open the HBS Faculty page
url = "https://www.hbs.edu/faculty/units/tom/Pages/faculty.aspx"
driver.get(url)

# Find faculty elements
faculty_list = driver.find_elements(By.CSS_SELECTOR, "div.media")

# Extract faculty names and titles
data = []
for faculty in faculty_list:
    try:
        name = faculty.find_element(By.CSS_SELECTOR, "h2 a").text.strip()
        title = faculty.find_element(By.CSS_SELECTOR, "div.nu").text.strip()
        data.append([name, title])
    except:
        continue

# Close the driver
driver.quit()

# Save to CSV
csv_filename = "hbs_faculty.csv"
df = pd.DataFrame(data, columns=["Name", "Title"])
df.to_csv(csv_filename, index=False)

print(f"Data successfully saved to {csv_filename}")