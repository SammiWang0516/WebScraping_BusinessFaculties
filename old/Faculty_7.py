#MIT  __WORKING__

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import pandas as pd
import time

# Set up Selenium WebDriver
service = Service('/usr/local/bin/chromedriver')  # Update with your chromedriver path
options = webdriver.ChromeOptions()
options.add_argument('--headless')  # Run in headless mode (no browser window)
driver = webdriver.Chrome(service=service, options=options)

# Load the MIT Sloan Faculty Directory
url = "https://mitsloan.mit.edu/faculty/faculty-directory#all"
driver.get(url)
time.sleep(5)  # Allow page to load

# Extract the page source and parse with BeautifulSoup
soup = BeautifulSoup(driver.page_source, 'html.parser')

# Close the browser
driver.quit()

# Extract all departments
faculty_sections = soup.find_all("header", class_="directory--group-header")

# Prepare list for storing data
faculty_data = []

# Iterate through each department section
for section in faculty_sections:
    h3_tag = section.find("h3", class_="directory--group-title jump-header")  # Get the h3 tag inside header
    if not h3_tag:
        continue

    # Extract department name, removing the <a> text inside h3
    department = h3_tag.get_text(" ", strip=True).split("  ")[0]  # Extract text and remove the <a> part

    # Find the next <dl> (faculty list) after this header
    dl_element = section.find_next("dl", class_="directory--group-list")

    if dl_element:
        faculty_members = dl_element.find_all("dt", class_="directory--item-title")
        titles = dl_element.find_all("dd", class_="directory--item-def")

        for faculty, title in zip(faculty_members, titles):
            name = faculty.get_text(strip=True)
            title_list = [t.get_text(strip=True) for t in title.find_all("div")]
            title_str = "; ".join(title_list)  # Combine multiple titles into one string

            faculty_data.append([name, title_str, department])

# Save data to CSV
df = pd.DataFrame(faculty_data, columns=["Name", "Title", "Department"])
df.to_csv("mit_faculty.csv", index=False, encoding="utf-8")

print("Data saved successfully to mit_faculty.csv")