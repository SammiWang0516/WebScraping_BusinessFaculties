#NYU __WORKING__


from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import csv

# Set up the Chrome WebDriver
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # Run browser in headless mode (no UI)
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# Open the target website
url = 'https://www.stern.nyu.edu/faculty/search_department_form'
driver.get(url)

# Wait for the page to fully load
WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'more')))

# Open the CSV file to store the data
with open('stern_faculty_selenium3.csv', mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(['Department', 'Faculty Name', 'Title'])  # No email column

    # Find all department elements
    departments = driver.find_elements(By.CSS_SELECTOR, 'tr')

    for dept in departments:
        department_name = "N/A"  # Initialize with default

        try:
            # Extract department name
            dept_link = dept.find_elements(By.TAG_NAME, 'a')  # Using find_elements to avoid exceptions
            if dept_link:
                department_name = dept_link[0].text.strip()

            # Check if department has a "more" button to reveal faculty
            more_div = dept.find_elements(By.CLASS_NAME, 'more')
            if more_div:
                view_faculty_link = more_div[0].find_elements(By.TAG_NAME, 'a')
                if view_faculty_link:
                    ActionChains(driver).move_to_element(view_faculty_link[0]).click().perform()
                    WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, './/table//tr')))

            # Extract faculty rows
            faculty_table = dept.find_elements(By.XPATH, './/table//tr')

            for row in faculty_table:
                cols = row.find_elements(By.TAG_NAME, 'td')
                if len(cols) > 0:
                    # Extract faculty name and title
                    faculty_name_tag = cols[0].find_elements(By.TAG_NAME, 'a')
                    faculty_title_tag = cols[0].find_elements(By.TAG_NAME, 'i')

                    faculty_name = faculty_name_tag[0].text.strip() if faculty_name_tag else 'N/A'
                    faculty_title = faculty_title_tag[0].text.strip() if faculty_title_tag else 'N/A'

                    # Write to CSV
                    writer.writerow([department_name, faculty_name, faculty_title])

        except Exception as e:
            print(f"Error processing department: {department_name}. Error: {e}")

# Close the WebDriver
driver.quit()

print("Data scraping completed and saved to stern_faculty_selenium2.csv")