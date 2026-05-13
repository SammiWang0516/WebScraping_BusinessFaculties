from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd

web = 'https://merage.uci.edu/research-faculty/faculty-directory/index.html'

# Specify Chrome binary path if necessary
chrome_options = Options()
chrome_options.add_experimental_option("detach", True)
chrome_options.binary_location = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"  # Update this path if needed

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)
driver.get(web)


# Wait for the elements to load
wait = WebDriverWait(driver, 5)  # Wait up to 5 seconds

page = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//tr[contains(@class,"deptRow")]')))

time.sleep(1)
name=[]
title=[]
dept=[]
email=[]
for pg in page:
    try:
        details=pg.find_elements(By.XPATH, './/td')[0].text.split('\n')
        title.append(details[1])
        dept.append(details[2])
        email.append(pg.find_elements(By.XPATH, './/a')[1].text)
        name.append(details[0])  #name should be at last or else A_Z are also added to name list
    except:
        continue

print(len(page),len(name),len(title),len(dept),len(email))
driver.quit()
df=pd.DataFrame({'Name':name, 'Title':title, 'Department':dept, 'Email':email})
df.to_csv('uci.csv', index=False)

