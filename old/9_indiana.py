from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd
from selenium.webdriver.support.ui import Select


web = 'https://kelley.iu.edu/faculty-research/faculty-directory/index.html'

# Specify Chrome binary path if necessary
chrome_options = Options()
chrome_options.add_experimental_option("detach", True)
chrome_options.binary_location = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"  # Update this path if needed

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)
driver.get(web)

names = []
emails = []
spec = []
titles = []
loc = []
dept=[]

# Wait for the elements to load
wait = WebDriverWait(driver, 15)  # Wait up to 15 seconds

all=wait.until(EC.presence_of_element_located((By.XPATH, '//button[@id="status-all"]')))
driver.execute_script("arguments[0].click();", all)

select_element = wait.until(EC.presence_of_element_located((By.XPATH, '//select')))
select = Select(select_element)
optiontxt = [option.text for option in select.options[1:]] 

for option in optiontxt:
    select_element = wait.until(EC.presence_of_element_located((By.XPATH, '//select')))
    select = Select(select_element)
    select.select_by_visible_text(option)
    srch=wait.until(EC.presence_of_element_located((By.XPATH, '//button[@id="searchFaculty"]')))
    driver.execute_script("arguments[0].click();", srch)
    time.sleep(1)
    # Locate all letters once before the loop
    letters = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//a[contains(@class,"char-select")]')))
    # Iterate through all the letters
    for i in range(len(letters)):
        try:
            # Re-locate the letters to avoid stale elements
            letters = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//a[contains(@class,"char-select")]')))
            # Click the current letter
            driver.execute_script("arguments[0].click();", letters[i])
            time.sleep(1)
            # Wait for the new content to load
            page = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//div[contains(@class,"faculty-directory grid thirds")]')))
            # Extract data from the page
            for pg in page:
                elm = pg.find_elements(By.XPATH, './/div[contains(@class,"text")]') 
                if len(elm) > 0:
                    try:
                        names.append(elm[0].find_elements(By.XPATH, './/a')[0].text)
                        dept.append(option)
                    except:
                        continue
                    try:
                        emails.append(elm[0].find_elements(By.XPATH, './/a')[1].text)
                    except:
                        emails.append("")
                    try:
                        spec.append(elm[1].text)
                    except:
                        spec.append("")
                    try:
                        para = elm[0].find_elements(By.XPATH, './/p')[0].text
                        para = para.split('\n')
                        titles.append(para[0])
                        loc.append(' '.join(para[2:]))
                    except:
                        titles.append("")
                        loc.append("")
                else:
                    print("No elements found in this page block")

        except Exception as e:
            print(f"Error while processing letter {i}: {e}")

# Print results
"""print("Names:", len(names))
print("Emails:", len(emails))
print("Titles:", len(titles))
print("Specializations:", len(spec))
print("Locations:", len(loc))"""

# Close the browser
driver.quit()
pd.DataFrame({"Name": names, "Department": dept, "Email": emails, "Title": titles, "Specialization": spec, "Location": loc}).to_csv("indiana.csv", index=False)