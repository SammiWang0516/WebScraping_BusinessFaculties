from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select

import time
import pandas as pd

web = 'https://eccles.utah.edu/directory/'

chrome_options = Options()
chrome_options.add_experimental_option("detach", True)
chrome_options.binary_location = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"  # Update this path if needed

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)
driver.get(web)

wait = WebDriverWait(driver, 200)

fac_name = []
fac_dept = []
fac_title = []
fac_url = []

last_height = 0
while True:    
    # Scroll down to load more elements
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(6)  
    new_height = driver.execute_script("return document.body.scrollHeight")
    if new_height == last_height:
        break  # Exit the loop if no new content is loaded
    last_height = new_height

elems = driver.find_elements(By.XPATH, '//div[@class="team-member"]')
for e in elems:
    name = e.find_element(By.XPATH, './/div[@class="team-title"]').text
    fac_name.append(name)
    fac_dept.append(e.find_element(By.XPATH, './/div[@class="team-department"]').text)
    try:
        fac_title.append(e.find_element(By.XPATH, './/div[@class="team-position"]').text)
    except:
        fac_title.append("")
    try:
        fac_url.append(e.find_element(By.XPATH, './/a').get_attribute('href'))
    except:
        fac_url.append("")
driver.quit()
df = pd.DataFrame({'Name': fac_name, 'Title': fac_title, 'Url': fac_url, 'Department':fac_dept})
df.to_csv("utah.csv", index=False)