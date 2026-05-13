import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Path to ChromeDriver (update if needed)
chrome_driver_path = "/usr/local/bin/chromedriver"

# Set up Chrome WebDriver with options
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run in headless mode
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

service = Service(chrome_driver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)

# Open faculty page
url = "https://wpcarey.asu.edu/people/departments/accountancy"
driver.get(url)

# Function to scrape faculty data
def scrape_faculty():
    data = []
    faculty_list = driver.find_elements(By.CSS_SELECTOR, "div.uds-person-profile")

    for faculty in faculty_list:
        try:
            # Extract name
            name_element = faculty.find_element(By.CSS_SELECTOR, "div.person a")
            name = name_element.text.strip() if name_element else "N/A"

            # Extract title
            title_element = faculty.find_element(By.CSS_SELECTOR, "div.person-profession h4")
            title = title_element.text.strip() if title_element else "N/A"

            # Store faculty data
            data.append([name, title])

        except Exception as e:
            print(f"Error processing faculty: {e}")
            continue

    return data

# Initialize data storage
faculty_data = []

# Get the total number of pages from the pagination
try:
    pagination_buttons = driver.find_elements(By.CSS_SELECTOR, "ul.pagination li.page-item button.page-link")
    page_numbers = [btn.text for btn in pagination_buttons if btn.text.isdigit()]
    total_pages = max(map(int, page_numbers)) if page_numbers else 1  # Get the highest page number
except Exception as e:
    print("Failed to retrieve total pages. Defaulting to 1.")
    total_pages = 1

# Loop through all pages
for page_num in range(1, total_pages + 1):
    print(f"Scraping page {page_num}...")

    # Scrape data from the current page
    faculty_data.extend(scrape_faculty())

    if page_num < total_pages:  # Don't click next on the last page
        try:
            # Find and click the next page button based on the page number
            next_page_button = driver.find_element(By.XPATH, f'//*[@id="webdir-container-1348"]/div/div[2]/div/div/nav/ul/li[3]/button')
            next_page_button.click()
            print(f"Moved to page {page_num + 1}...")
            time.sleep(3)  # Allow time for the new page to load

        except Exception as e:
            print(f"No button found for page {page_num + 1}, stopping pagination.")
            break

driver.quit()

csv_filename = "asu_wpcarey_faculty.csv"
df = pd.DataFrame(faculty_data, columns=["Name", "Title"])
df.to_csv(csv_filename, index=False)

print(f"Successfully scraped {len(faculty_data)} faculty members and saved to {csv_filename}")