#University of Chicago (Booth) __WORKING__

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import time
import csv

# Set up Chrome options
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run in headless mode (no UI)
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920x1080")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# Set path to chromedriver
chromedriver_path = "/usr/local/bin/chromedriver"  # Update this to your chromedriver path
service = Service(chromedriver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)


# Target URL
url = "https://www.chicagobooth.edu/faculty/academic-areas/strategy-and-leadership#sort=%40foldingchild%20ascending"
driver.get(url)
time.sleep(5)  # Allow time for page to load

# Extract faculty data
faculty_list = []
faculty_cards = driver.find_elements(By.CLASS_NAME, "coveo-card-layout")

for card in faculty_cards:
    try:
        name = card.find_element(By.TAG_NAME, "h2").text.strip()
        title = card.find_element(By.TAG_NAME, "p").text.strip()
        
        
        faculty_list.append([name, title])
    except Exception as e:
        print(f"Error extracting faculty data: {e}")

# Save data to CSV
csv_filename = "ChicagoBooth_Accounting_Faculty.csv"
with open(csv_filename, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Name", "Title"])
    writer.writerows(faculty_list)

driver.quit()
print(f"Scraped {len(faculty_list)} faculty members. Data saved to {csv_filename}.")
