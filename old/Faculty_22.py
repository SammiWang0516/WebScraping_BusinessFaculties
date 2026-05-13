#Northwestern University (Kellogg School of Management) __WORKING__

import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains

# Setup Chrome WebDriver
chrome_driver_path = "/usr/local/bin/chromedriver"  # Update this path if needed
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run in headless mode
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

service = Service(chrome_driver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)

# Open the faculty directory page
url = "https://www.kellogg.northwestern.edu/faculty/faculty_directory/?academicDepartments=Strategy"
driver.get(url)

# Wait for JavaScript to load
time.sleep(5)

# Function to click "More Faculty" button safely
def click_more_faculty():
    max_clicks = 10  # Prevent infinite loops
    prev_count = 0  # Track previous number of faculty members

    for _ in range(max_clicks):
        try:
            # Get current faculty count
            faculty_list = driver.find_elements(By.CLASS_NAME, "faculty-directory-listing__faculty-member")
            current_count = len(faculty_list)

            # If no new faculty are loaded, stop clicking
            if current_count == prev_count:
                print("All faculty loaded....")
                break

            # Try clicking the "More Faculty" button
            more_faculty_button = driver.find_element(By.XPATH, "//button[contains(text(), 'More Faculty')]")
            ActionChains(driver).move_to_element(more_faculty_button).click(more_faculty_button).perform()
            time.sleep(3)  # Allow new data to load

            # Update previous faculty count
            prev_count = current_count
        except:
            break  # Exit if button is not found

# Click "More Faculty" until all faculty are loaded
click_more_faculty()

# Wait for final content to load
time.sleep(5)

# Find all faculty members
faculty_list = driver.find_elements(By.CLASS_NAME, "faculty-directory-listing__faculty-member")

# Store faculty data
faculty_data = []

for faculty in faculty_list:
    try:
        # Extract name
        name = faculty.find_element(By.CLASS_NAME, "faculty-directory-listing__name").text.strip()

        # Extract title(s)
        title_element = faculty.find_element(By.CLASS_NAME, "faculty-directory-listing__title")
        titles = title_element.text.split(";")  # Split multiple titles

        # Append each title as a separate row
        for title in titles:
            faculty_data.append([name, title.strip()])
    except:
        continue  # Skip if data isn't found

driver.quit()

csv_filename = "kellogg_faculty.csv"
df = pd.DataFrame(faculty_data, columns=["Name", "Title"])
df.to_csv(csv_filename, index=False)

print(f"Data successfully saved to {csv_filename}")