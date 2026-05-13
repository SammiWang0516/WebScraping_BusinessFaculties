#Yale University (School of Management)   __WORKING__

import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys

# Path to ChromeDriver (update if needed)
chrome_driver_path = "/usr/local/bin/chromedriver"

# Set up Chrome WebDriver with options
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run in headless mode
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

service = Service(chrome_driver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)

# Open page
url = "https://som.yale.edu/faculty-research/faculty-directory?q=/faculty-research/faculty-directory%3Fq%3D/faculty-research/faculty-directory%3Fq%3D/faculty-research/faculty-directory%3Fq%3D/faculty-research/faculty-directory%3Fq%3D/faculty-research/faculty-directory%3Fq%3D/faculty-research/faculty-directory%3Fq%3D/faculty-research/faculty-directory%3Fq%3D/faculty-research/faculty-directory%3Fq%3D/faculty-research/faculty-directory%3Fq%3D/faculty-research/faculty-directory%3Fq%3D/faculty-research/faculty-directory%3Fq%3D/faculty-research/faculty-directory%3Fq%3D/faculty-research/faculty-directory%3Fq%3D/faculty-research/faculty-directory%3Fq%3D/faculty-research/faculty-directory%3Fq%3D/faculty-research/faculty-directory%3Ffaculty_directory%5B0%5D%3Dfaculty_discipline%3AEconomics&viewsreference%5Bcompressed%5D=eJxdkMEKwyAQRP9lzznE0kKbn5FtXe2CmqAmJYT8exXbSHuQdZw3s-AGChPCsAEGMzvyCQY_W9vBhIbCV4xaRzosy46zAOggcbIEQ793QB7vlpTMYGJv4m9pu7Z8nUfJZ-5ld8ikzIfTKtM6FTc_ogk4PeEfYJXt21n0p2ZpJqukR1eiVSxMrygDacrEgxobaOHIo69FohcXcS1VNcaJnFRkyzf1-xswiWm_&faculty_directory%5B0%5D=faculty_discipline%3AManagement"
driver.get(url)

time.sleep(5)

#Scroll down to load all faculty members
scroll_pause_time = 3  # Adjust if needed
last_height = driver.execute_script("return document.body.scrollHeight")

while True:
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(scroll_pause_time)  # Wait for new faculty to load

    new_height = driver.execute_script("return document.body.scrollHeight")
    if new_height == last_height:
        print("Reached the bottom of the page. All faculty members should be loaded.")
        break
    last_height = new_height

#Scrape faculty data
faculty_list = driver.find_elements(By.CSS_SELECTOR, "div.som-row.som-row--faculty")
data = []

print(f"Found {len(faculty_list)} faculty members to scrape...")

for faculty in faculty_list:
    try:
        # Extract faculty name
        name = faculty.find_element(By.CSS_SELECTOR, "h3.som-row__heading a").text.strip()

        # Extract faculty title
        title_element = faculty.find_element(By.CSS_SELECTOR, "span.som-row__job-title")
        title = title_element.text.strip() if title_element else "N/A"

        # Store faculty data
        data.append([name, title])

    except Exception as e:
        print(f"Error processing faculty: {e}")
        continue

csv_filename = "yale_som_faculty.csv"
df = pd.DataFrame(data, columns=["Name", "Title"])
df.to_csv(csv_filename, index=False)

driver.quit()

print(f"Successfully scraped {len(data)} faculty members and saved to {csv_filename}")