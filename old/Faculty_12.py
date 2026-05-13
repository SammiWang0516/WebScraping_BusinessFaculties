#Cornell __NOTWORKING__

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import time

# Setup Selenium WebDriver
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # Run in headless mode
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# Open Cornell Faculty Page (Accounting)
url = "https://business.cornell.edu/faculty-research/search/?expertise=Accounting"
driver.get(url)

# Wait until the tbody is fully loaded
try:
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.TAG_NAME, "tbody"))
    )
    print("Table loaded successfully.")
except Exception as e:
    print("Timeout: Table did not load.")
    driver.quit()
    exit()

# Get updated page source after waiting
soup = BeautifulSoup(driver.page_source, "html.parser")
driver.quit()  # Close browser after page is loaded

# List to store faculty data
faculty_data = []

# Find the <tbody> element
tbody = soup.find("tbody")
if tbody:
    faculty_rows = tbody.find_all("tr")  # Only extract rows under <tbody>

    for row in faculty_rows:
        # Extract Name
        name_tag = row.find("td", class_="fac-search-results-table__name")
        name = name_tag.find("a").text.strip() if name_tag and name_tag.find("a") else "N/A"

        # Extract Titles (handling multiple titles)
        title_cell = row.find("td", class_="fac-search-results-table__titles")
        if title_cell:
            title_tags = title_cell.find_all("span")
            titles = [title.text.strip() for title in title_tags if title.text.strip()]
        else:
            titles = ["N/A"]

        # Store Each Title as a Separate Row
        for title in titles:
            faculty_data.append([name, title])

    print(f"Scraped {len(faculty_data)} faculty records.")

else:
    print("No <tbody> found. Check the website structure.")

# Save to CSV
df = pd.DataFrame(faculty_data, columns=["Name", "Title"])
df.to_csv("cornell_faculty_fixed.csv", index=False)

print("Data saved to cornell_faculty_fixed.csv")