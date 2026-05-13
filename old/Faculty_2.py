#___WORKING__ Faculty list at UTDallas. You will have to reuse the link for each of the department

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import csv
import time

# Set up Selenium WebDriver
options = Options()
options.add_argument("--headless")  # Run in headless mode (no browser window)
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920x1080")

# Initialize WebDriver
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

# URL of the faculty listing page
url = "https://jindal.utdallas.edu/faculty/#7"
driver.get(url)

# Wait for JavaScript to load (adjust sleep time if needed)
time.sleep(5)  # You can use WebDriverWait for better performance

# Get page source and parse with BeautifulSoup
soup = BeautifulSoup(driver.page_source, "html.parser")

# Find all faculty list items
faculty_list = []

for faculty in soup.find_all('div', class_='stat-box white left50'):
    name_tag = faculty.find('a')  # Faculty name
    title_tag = faculty.find('h4')  # Faculty title
    email_tag = faculty.find('a', href=lambda x: x and 'mailto:' in x)  # Email extraction

    name = name_tag.get_text(strip=True) if name_tag else "N/A"
    title = title_tag.get_text(strip=True) if title_tag else "N/A"
    email = email_tag.get('href').replace('mailto:', '') if email_tag else "N/A"

    faculty_list.append([name, title, email])

# Close the Selenium WebDriver
driver.quit()

# Save data to a CSV file
csv_filename = "UTDallas_faculty.csv"
with open(csv_filename, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["Name", "Title", "Email"])
    writer.writerows(faculty_list)

print(f"Scraped {len(faculty_list)} faculty members. Data saved to {csv_filename}")