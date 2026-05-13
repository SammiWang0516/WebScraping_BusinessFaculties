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


web='https://goizueta.emory.edu/faculty/profiles'

chrome_options = Options()
chrome_options.add_experimental_option("detach", True)
chrome_options.binary_location = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"  # Update this path if needed

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)
driver.get(web)

wait = WebDriverWait(driver, 20)  
select_element = wait.until(EC.presence_of_element_located((By.XPATH, '//select[contains(@id,"edit-department-id")]')))
select = Select(select_element)
optiontxt = [option.text for option in select.options[1:]] 

fac_name=[]
fac_dept=[]
fac_title=[]


for option in optiontxt:
    select_element = wait.until(EC.presence_of_element_located((By.XPATH, '//select[contains(@id,"edit-department-id")]')))
    select = Select(select_element)
    select.select_by_visible_text(option)
    sbmt=wait.until(EC.presence_of_element_located((By.XPATH, '//button[@type="submit"]')))
    driver.execute_script("arguments[0].click();", sbmt)
    time.sleep(2)

    elems=wait.until(EC.presence_of_all_elements_located((By.XPATH, '//div[@class="faculty-card__content"]')))
    for e in elems:
        fac_name.append(e.find_element(By.XPATH,'.//div[contains(@class,"heading--wrapper")]').text)
        fac_dept.append(option)
        fac_title.append(e.find_element(By.XPATH,'.//div[contains(@class,"content--body")]').text)        
    try:
        nxtpgs=wait.until(EC.presence_of_all_elements_located((By.XPATH, '//li[@class="pager__item"]/a')))
        for n in nxtpgs:
            driver.execute_script("arguments[0].click();",n)
            time.sleep(2)
            elems=wait.until(EC.presence_of_all_elements_located((By.XPATH, '//div[@class="faculty-card__content"]')))
            for e in elems:
                fac_name.append(e.find_element(By.XPATH,'.//div[contains(@class,"heading--wrapper")]').text)
                fac_dept.append(option)
                fac_title.append(e.find_element(By.XPATH,'.//div[contains(@class,"content--body")]').text)
    except:
        continue       

driver.quit()
df=pd.DataFrame({'Name':fac_name,'Department':fac_dept,'Title':fac_title})
df.to_csv("emory_goizueta.csv",index=False)