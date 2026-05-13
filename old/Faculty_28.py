#Texas A&M University at College Station (Mays Business School) 



import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# Path to ChromeDriver (update if needed)
chrome_driver_path = "/usr/local/bin/chromedriver"

# Set up Chrome WebDriver with options
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run in headless mode
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

service = Service(chrome_driver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)

# Open the directory page
url = "https://mays.tamu.edu/faculty/?department=4&fullname="
driver.get(url)

time.sleep(5)

#Scrape data
faculty_list = driver.find_elements(By.CSS_SELECTOR, "div.directory-col")
data = []

for faculty in faculty_list:
    try:
        # Extract name
        name = faculty.find_element(By.CSS_SELECTOR, "div.heading3 a").text.strip()

        # Extract all titles (each title is in a <p> tag)
        title_elements = faculty.find_elements(By.CSS_SELECTOR, "div.listing-overlay p")
        titles = "; ".join([t.text.split("\n")[0].strip() for t in title_elements if t.text.strip()])  # Keep multiple titles in one row

        # Store faculty data
        data.append([name, titles])

    except Exception as e:
        print(f"Error processing faculty: {e}")
        continue


csv_filename = "texas_am_mays_accounting_faculty.csv"
df = pd.DataFrame(data, columns=["Name", "Title"])
df.to_csv(csv_filename, index=False)

driver.quit()

print(f"Data successfully saved to {csv_filename}")