#Indiana university Kelly __NOTWORKING__

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import csv
import time

# Setup Selenium WebDriver
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # Run browser in headless mode
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# Open the faculty directory page
url = "https://kelley.iu.edu/faculty-research/faculty-directory/index.html"
driver.get(url)

# Wait for the page to load
wait = WebDriverWait(driver, 10)

# Click the department dropdown
dept_dropdown = wait.until(EC.element_to_be_clickable((By.ID, "departmentid")))  # Adjust ID if needed
dept_dropdown.click()
time.sleep(1)  # Small delay to ensure dropdown expands

# Select "Accounting" from the dropdown
accounting_option = wait.until(EC.element_to_be_clickable((By.XPATH, "//option[contains(text(), 'Accounting')]")))
accounting_option.click()
time.sleep(5)  # Wait for page to refresh

# Open CSV file for writing
with open("kelley_faculty.csv", mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["Faculty Name", "Title", "Research Interest"])

    # Find all faculty entries
    faculty_blocks = driver.find_elements(By.CSS_SELECTOR, ".faculty-directory.grid.thirds")

    for faculty in faculty_blocks:
        try:
            # Extract faculty name
            name_tag = faculty.find_element(By.CSS_SELECTOR, ".grid-item:nth-child(2) h3 a")
            faculty_name = name_tag.text.strip()

            # Extract faculty title
            title_tag = faculty.find_element(By.CSS_SELECTOR, ".grid-item:nth-child(2) p")
            faculty_title = title_tag.text.split("\n")[0].strip()

            # Extract research interest
            research_tag = faculty.find_element(By.CSS_SELECTOR, ".grid-item:nth-child(3) p")
            research_interest = research_tag.text.strip()

            # Write to CSV
            writer.writerow([faculty_name, faculty_title, research_interest])

        except Exception as e:
            print(f"Skipping an entry due to an error: {e}")

# Close WebDriver
driver.quit()

print("Scraping complete! Data saved in kelley_faculty.csv")