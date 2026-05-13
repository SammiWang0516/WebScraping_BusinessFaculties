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


web='https://business.wisc.edu/directory/'

chrome_options = Options()
chrome_options.add_experimental_option("detach", True)
chrome_options.binary_location = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"  # Update this path if needed

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)
driver.get(web)

wait = WebDriverWait(driver, 20)  
select_element = wait.until(EC.presence_of_element_located((By.XPATH, '//div[contains(@class,"profile_department")]/select')))
select = Select(select_element)
optiontxt = [option.text for option in select.options[1:]] 

fac_name=[]
fac_dept=[]
fac_title=[]
fac_email=[]
fac_expertise=[]

for option in optiontxt:
    select_element = wait.until(EC.presence_of_element_located((By.XPATH, '//div[contains(@class,"profile_department")]/select')))
    select = Select(select_element)
    select.select_by_visible_text(option)
    time.sleep(6)     #Increase this time for slow connections- bottleneck
    while True:
        try:
            elems=wait.until(EC.presence_of_all_elements_located((By.XPATH, '//div[contains(@class,"col mb-4")]')))
            for e in elems:
                fac_name.append(e.find_element(By.XPATH,'.//h3[contains(@class,"card-title")]').text)
                fac_dept.append(option)
                try:
                    fac_title.append(e.find_element(By.XPATH,'.//div[contains(@class,"directory-title")]').text)
                except:
                    fac_title.append("")
                try:
                    fac_email.append(e.find_element(By.XPATH,'.//div[contains(@class,"email-title")]').text)
                except:
                    fac_email.append("")
                try:
                    fac_expertise.append(e.find_element(By.XPATH,'.//div[contains(@class,"department")]').text)
                except:
                    fac_expertise.append("")
           
            nxtpg=wait.until(EC.presence_of_element_located((By.XPATH, '//div[@class="facetwp-pager"]/a[contains(@class,"facetwp-page next")]')))
            driver.execute_script("arguments[0].click();", nxtpg)
            time.sleep(6) #Bottleneck 2
        except:
            time.sleep(1)
            break

driver.quit()
df=pd.DataFrame({'Name':fac_name,'Department':fac_dept,'Title':fac_title,'Expertise':fac_expertise,'Email':fac_email})
df.to_csv("wisconsin_fix.csv",index=False)