#Purdue University (Mitchell E. Daniels, Jr. School of Business / Krannert School of Management) 
# __WORKING__
#Update needed = change url, and change the export file name

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
url = "https://business.purdue.edu/directory/view.php?LastName=&FirstName=&search=FacArea&FacAreaList=58&StaffDeptList=71&Keyword=&Submit=Search+Directory"
driver.get(url)

time.sleep(5)

#Scrape data
faculty_rows = driver.find_elements(By.XPATH, "//tr[@bgcolor='#e9e9e9']")
data = []

for faculty in faculty_rows:
    try:
        # Extract name
        name = faculty.find_element(By.XPATH, ".//td[1]//strong").text.strip()

        # Extract all text from the same td but **after** the name
        full_text = faculty.find_element(By.XPATH, ".//td[1]").text.strip()
        title = full_text.replace(name, "").strip().replace("\n", "; ")

        # Store faculty data
        data.append([name, title])

    except Exception as e:
        print(f"Error processing faculty: {e}")
        continue


csv_filename = "purdue_krannert_accounting_faculty.csv"
df = pd.DataFrame(data, columns=["Name", "Title"])
df.to_csv(csv_filename, index=False)

driver.quit()

print(f"Data successfully saved to {csv_filename}")