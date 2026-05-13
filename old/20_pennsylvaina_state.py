import email
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


web = 'https://directory.smeal.psu.edu/'

# Specify Chrome binary path if necessary
chrome_options = Options()
chrome_options.add_experimental_option("detach", True)
chrome_options.binary_location = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"  # Update this path if needed

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)
driver.get(web)

names = []
url=[]
dept = []
phone = []
eml = []
loc = []

# Wait for the elements to load
wait = WebDriverWait(driver, 15)  # Wait up to 15 seconds

letters = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//div[contains(@class,"btn-group")]/a')))
# Iterate through all the letters
for i in range(len(letters)):
    # Click the current letter
    letters = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//div[contains(@class,"btn-group")]/a')))
    driver.execute_script("arguments[0].click();", letters[i])
    time.sleep(1)
    # Wait for the new content to load
    facs = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//div[contains(@class,"media-body")]')))
    # Extract data from the page
    for f in facs:
        names.append(f.find_element(By.XPATH, './/strong[@class="media-heading"]/a').text)
        url.append(f.find_element(By.XPATH, './/strong[@class="media-heading"]/a').get_attribute('href'))
        try:
            dept.append(f.find_element(By.XPATH, './/p[contains(@style,"padding-top")]/a').text)
        except: 
            dept.append("")
        try:
            ph=f.find_elements(By.XPATH, './/p')[1].text
            if '@' not in ph:
                phone.append(ph)
            else:
                phone.append("")
        except: 
            phone.append("")
        try:
            em=f.find_elements(By.XPATH, './/p')[1].find_element(By.XPATH,'.//a').get_attribute('href').replace('mailto:','')
            if '@' in em:
                eml.append(em)
            else:
                eml.append("")
        except:
            eml.append("")
        try:
            loc.append(f.find_elements(By.XPATH, './/p')[2].text)
        except:
            loc.append("")
           
titles=[]
for u in url:
    try:
        driver.get(u)
        titles.append(driver.find_element(By.XPATH,'//p[@class="dir-titles"]').text)
        time.sleep(1)
    except:
        titles.append("")

driver.quit()
df=pd.DataFrame ({'Name': names,'URL': url,'Department': dept,'Title':titles,'Phone': phone,'Email': eml,'Location': loc})
df.to_csv('pennstate.csv', index=False)