#University of Illinois at Urbana-Champaign (Gies College of Business) __WORKING__

'''import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select

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
url = "https://giesbusiness.illinois.edu/faculty-research/faculty-profiles#page-1"
driver.get(url)

# Wait for page to load
time.sleep(5)

# Locate the department dropdown
department_dropdown = driver.find_element(By.ID, "department")

# Select "Accountancy" from dropdown
select = Select(department_dropdown)
select.select_by_visible_text("Finance")

# Wait for the page to reload with new results
time.sleep(5)

# Function to extract faculty data
def scrape_faculty():
    faculty_list = driver.find_elements(By.CSS_SELECTOR, "ul.results li")
    data = []

    for faculty in faculty_list:
        try:
            # Extract name
            name = faculty.find_element(By.CSS_SELECTOR, "div.faculty-name a").text.strip()

            # Extract titles and combine them into a single string
            title_element = faculty.find_element(By.CSS_SELECTOR, "div.faculty-description")
            titles = title_element.text.replace(" and ", ", ")  # Format multiple titles

            # Store the faculty data
            data.append([name, titles])

        except Exception as e:
            print(f"Error processing faculty: {e}")
            continue

    return data

# Scrape faculty from page 1
faculty_data = scrape_faculty()

# Loop through pages 2 and 3
for page_num in range(2, 4):  # Pages 2 and 3
    try:
        next_button = driver.find_element(By.LINK_TEXT, str(page_num))
        next_button.click()
        time.sleep(5)  # Wait for new results to load

        # Scrape faculty from the next page
        faculty_data.extend(scrape_faculty())

    except Exception as e:
        print(f"No page {page_num} found or failed to navigate.")
        break

# Close the browser
driver.quit()

# Save to CSV
csv_filename = "gies_business_accountancy_faculty.csv"
df = pd.DataFrame(faculty_data, columns=["Name", "Title"])
df.to_csv(csv_filename, index=False)

print(f"Data successfully saved to {csv_filename}")'''


import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select

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
url = "https://giesbusiness.illinois.edu/faculty-research/faculty-profiles"
driver.get(url)

time.sleep(5)

# Function to extract faculty data
def scrape_faculty():
    faculty_list = driver.find_elements(By.CSS_SELECTOR, "ul.results li")
    data = []

    for faculty in faculty_list:
        try:
            # Extract name
            name = faculty.find_element(By.CSS_SELECTOR, "div.faculty-name a").text.strip()

            # Extract titles and combine them into a single string
            title_element = faculty.find_element(By.CSS_SELECTOR, "div.faculty-description")
            titles = title_element.text.replace(" and ", ", ")  # Format multiple titles

            # Store the faculty data
            data.append([name, titles])

        except Exception as e:
            print(f"Error processing faculty: {e}")
            continue

    return data

# Function to select department and scrape
def select_department_and_scrape(department_value, filename):
    # Locate the department dropdown
    department_dropdown = driver.find_element(By.ID, "department")
    select = Select(department_dropdown)

    # Print available dropdown values
    available_values = [option.get_attribute("value") for option in select.options]
    print(f"Available values in dropdown: {available_values}")

    if department_value in available_values:
        print(f"Selecting department by value: {department_value}")

        # Select by value instead of visible text
        select.select_by_value(department_value)
        time.sleep(5)  # Wait for page reload

    else:
        print(f"Department '{department_value}' not found. Skipping.")
        return  # Skip if department not found

    # Scrape faculty from page 1
    faculty_data = scrape_faculty()

    # Loop through additional pages (if available)
    page_num = 2
    while True:
        try:
            next_button = driver.find_element(By.LINK_TEXT, str(page_num))
            next_button.click()
            time.sleep(5)  # Wait for new results to load

            # Scrape faculty from the next page
            faculty_data.extend(scrape_faculty())
            page_num += 1  # Move to the next page
        except:
            print(f" No more pages found for {department_value}. Moving to next department.")
            break

    # Save to CSV
    df = pd.DataFrame(faculty_data, columns=["Name", "Title"])
    df.to_csv(filename, index=False)
    print(f"Data successfully saved to {filename}")

# Run scraping for....
select_department_and_scrape("Strategy and Entrepreneurship[-]International Business[-]International Business", "gies_business_is_ops_faculty.csv")

# Close the browser
driver.quit()