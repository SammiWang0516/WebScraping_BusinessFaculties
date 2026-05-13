#UTexas_Austin McCombs __WORKING__

from selenium import webdriver
from bs4 import BeautifulSoup
import pandas as pd
import time

# Setup WebDriver
driver = webdriver.Chrome()
url = "https://www.mccombs.utexas.edu/faculty-and-research/faculty-directory?filter=true&department_taxonomy=marketing&page=5"
driver.get(url)

# Allow time for page to load
time.sleep(5)

# Get page source and parse with BeautifulSoup
soup = BeautifulSoup(driver.page_source, "html.parser")

# Close the browser
driver.quit()

# Use a set to track unique names and avoid duplication
unique_faculty = set()
faculty_data = []

# Find all faculty blocks
faculty_blocks = soup.find_all("div", class_="grid-item-cont")

for faculty in faculty_blocks:

    # Extract faculty name
    name_tag = faculty.find("div", class_="utm-faculty-card__name")
    name = name_tag.text.strip() if name_tag else "N/A"

    # Extract faculty title
    title_tag = faculty.find("p", class_="utm-faculty-card__title")
    title = title_tag.text.strip() if title_tag else "N/A"

    # Extract faculty department
    dept_tag = faculty.find("p", class_="utm-faculty-card__department")
    department = dept_tag.text.strip() if dept_tag else "N/A"

    # Only add unique names
    if name not in unique_faculty:
        unique_faculty.add(name)
        faculty_data.append([name, title, department])

# Save data to CSV
df = pd.DataFrame(faculty_data, columns=["Name", "Title", "Department"])
df.to_csv("mccombs_faculty.csv", index=False)

print("Scraping complete! Data saved to mccombs_faculty.csv")