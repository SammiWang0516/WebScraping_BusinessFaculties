#University of Southern California  __WORKING__


from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import pandas as pd

# Set up Selenium with ChromeDriver
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run in headless mode
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# Path to ChromeDriver (Ensure it's updated)
service = Service("/usr/local/bin/chromedriver")  # Update this with your actual path
driver = webdriver.Chrome(service=service, options=chrome_options)

# URL of the faculty directory
url = "https://www.marshall.usc.edu/faculty-research/faculty-directory?department=883"
driver.get(url)

# Wait for the page to load
time.sleep(5)

# Extract faculty list items
faculty_list = driver.find_elements(By.CSS_SELECTOR, "li.person-list-item")

# Store results
data = []

for faculty in faculty_list:
    try:
        name = faculty.find_element(By.CSS_SELECTOR, "h3.title").text.strip()
        position_elements = faculty.find_elements(By.CSS_SELECTOR, "ul.position-list li")

        # Combine multiple titles into a single string
        positions = ", ".join([pos.text.strip() for pos in position_elements if pos.text.strip()])

        # Append the data as a single row
        data.append([name, positions])

    except Exception as e:
        print(f"❌ Error processing faculty: {e}")
        continue

# Save to CSV
df = pd.DataFrame(data, columns=["Name", "Position"])
csv_filename = "usc_faculty_fixed.csv"
df.to_csv(csv_filename, index=False, encoding="utf-8")

print(f"✅ Successfully saved data to {csv_filename}")

# Close the browser
driver.quit()