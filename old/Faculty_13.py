#Duke Uni __WORKING__


from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd


# Setup Selenium WebDriver
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # Run in headless mode
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# Open Duke Fuqua Accounting Faculty Page
url = "https://areas.fuqua.duke.edu/strategy/?_gl=1*y30xlv*_gcl_au*MTAyODc3MTgxNC4xNzQxMTQyMDYw*_ga*MTc3NjQyNjE4LjE3NDExNDIwNjE.*_ga_1QY6PJLGK7*MTc0MTMxMzM3OC41LjEuMTc0MTMxNDI5OC42MC4wLjA."
driver.get(url)

# Wait for faculty section to load
try:
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "facultyCards"))
    )
    print("Faculty section loaded successfully.")
except Exception as e:
    print("Timeout: Faculty section did not load.")
    driver.quit()
    exit()

# Get page source and parse with BeautifulSoup
soup = BeautifulSoup(driver.page_source, "html.parser")
driver.quit()  # Close browser after page is loaded

# List to store faculty data
faculty_data = []

# Find all faculty blocks inside the facultyCards section
faculty_cards = soup.find("div", id="facultyCards")
if faculty_cards:
    faculty_profiles = faculty_cards.find_all("div", class_="profileModule")

    for faculty in faculty_profiles:
        # Extract faculty name
        name_tag = faculty.find("h4", class_="profileModule_title")
        name = name_tag.text.strip() if name_tag else "N/A"

        # Extract faculty title
        title_tag = faculty.find("span", class_="profileModule_subtitle")
        title = title_tag.text.strip() if title_tag else "N/A"

        # Add extracted data to the list
        faculty_data.append([name, title])

    print(f"Scraped {len(faculty_data)} faculty records.")

else:
    print("No faculty cards found. Check the website structure.")

# Save to CSV
df = pd.DataFrame(faculty_data, columns=["Name", "Title"])
df.to_csv("duke_fuqua_faculty.csv", index=False)

print("Data saved to duke_fuqua_faculty.csv")