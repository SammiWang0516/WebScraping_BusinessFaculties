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


web='https://www.scheller.gatech.edu/directory/index.html'

chrome_options = Options()
chrome_options.add_experimental_option("detach", True)
chrome_options.binary_location = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"  # Update this path if needed

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)
driver.get(web)

wait = WebDriverWait(driver, 20)  

filters=wait.until(EC.presence_of_all_elements_located((By.XPATH, '//input[contains(@class,"custom-checkbox filter1")]')))
for f in filters:
    driver.execute_script("arguments[0].click();", f)

fac_name=[]
fac_status=[]
fac_area=[]
fac_position=[]
fac_email=[]
time.sleep(5)
elems=wait.until(EC.presence_of_all_elements_located((By.XPATH, '//tr[contains(@class,"body-row--directory-cards")]')))
for e in elems:
    fac_name.append(e.find_element(By.XPATH,'.//td/div[@class="stylized-table__name"]/span').text)
    fac_position.append(e.find_element(By.XPATH,'.//td/div[@class="stylized-table__name"]/p').text)
    try:
        fac_status.append(e.find_element(By.XPATH,'.//td[3]').text)
    except:
        fac_status.append("")
    try:
        fac_area.append(e.find_element(By.XPATH,'.//td[4]').text)
    except:
        fac_area.append("")
    try:
        fac_email.append(e.find_element(By.XPATH,'.//td[5]/div/div/a').get_attribute('href').replace('mailto:',''))
    except:
        fac_email.append("")

driver.quit()
df=pd.DataFrame({'Name':fac_name,'Status':fac_status,'Area':fac_area,'Position':fac_position,'Email':fac_email})
df.to_csv("georgiatech.csv",index=False)