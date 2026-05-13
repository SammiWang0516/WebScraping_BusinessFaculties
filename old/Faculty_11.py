#Stanford __WORKING__

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import pandas as pd
import time

# Setup Selenium WebDriver
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # Run in headless mode
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# Open Stanford GSB Faculty Directory Page (Accounting)
url = "https://www.gsb.stanford.edu/faculty-research/faculty/academic-areas/political-economy"
driver.get(url)

# Wait for faculty list to load
WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.CLASS_NAME, "c-person--faculty-main-list"))
)

# Scroll down multiple times to load all faculty
scroll_pause_time = 3
last_height = driver.execute_script("return document.body.scrollHeight")

for _ in range(15):  # Scroll 15 times to ensure full page loads
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(scroll_pause_time)
    new_height = driver.execute_script("return document.body.scrollHeight")
    if new_height == last_height:
        break  # Stop if no more content loads
    last_height = new_height

# Get the full page source and parse it with BeautifulSoup
soup = BeautifulSoup(driver.page_source, "html.parser")

# Close the browser
driver.quit()

# List to store faculty data
faculty_data = []

# Find all faculty blocks
faculty_blocks = soup.find_all("div", class_="c-person c-person--faculty-main-list views-row")

for faculty in faculty_blocks:
    # Extract faculty name
    name = "N/A"
    name_tag = faculty.find("h3", class_="c-person__name c-person__name--faculty")
    if name_tag and name_tag.find("a"):
        name = name_tag.find("a").text.strip()

    # Extract faculty title
    title = "N/A"
    title_tag = faculty.find("div", class_="c-person__position c-person__position--faculty")
    if title_tag:
        title = title_tag.contents[0].strip()

    # Add extracted data to the list
    faculty_data.append([name, title])

# Save data to a CSV file
df = pd.DataFrame(faculty_data, columns=["Name", "Title"])
df.to_csv("stanford_gsb_faculty_fixed.csv", index=False)

print("Scraping complete! Data saved to stanford_gsb_faculty_fixed.csv")