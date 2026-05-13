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


web='https://damore-mckim.northeastern.edu/people/'

chrome_options = Options()
chrome_options.add_experimental_option("detach", True)
chrome_options.binary_location = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"  # Update this path if needed

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)
driver.get(web)

wait = WebDriverWait(driver, 20)  
select_element = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//ul[@class="filter-list person-filters__area__filter-list"]/li')))
optiontxt = [driver.execute_script("return arguments[0].textContent;", option).replace('\n','').replace('\t','') for option in select_element]
fac_name=[]
fac_dept=[]
fac_title=[]
fac_url=[]

for i in range(len(optiontxt)):
    sel = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//ul[@class="filter-list person-filters__area__filter-list"]/li')))[i].find_element(By.XPATH,'.//input')
    driver.execute_script("arguments[0].click();", sel)
    apply= wait.until(EC.presence_of_element_located((By.XPATH, '//button[@id="search-filter-button"]')))
    driver.execute_script("arguments[0].click();", apply)
    time.sleep(4)
    while True:
        try:
            elems=wait.until(EC.presence_of_all_elements_located((By.XPATH, '//div[@class="person-line-content"]'))) 
            for e in elems:
                fac_name.append(e.find_element(By.XPATH,'.//h3/a').text)
                fac_url.append(e.find_element(By.XPATH,'.//h3/a').get_attribute('href'))
                fac_dept.append(optiontxt[i])
                try:
                    fac_title.append(e.find_element(By.XPATH,'.//div').text)
                except:
                    fac_title.append("")           
            nxtpg=wait.until(EC.presence_of_element_located((By.XPATH, '//a[@class="next page-numbers"]')))
            driver.execute_script("arguments[0].click();", nxtpg)
            time.sleep(4)
        except:
            time.sleep(1)
            rst=wait.until(EC.presence_of_element_located((By.XPATH, '//button[@id="js-reset-search-filter-button"]')))
            driver.execute_script("arguments[0].click();", rst)
            break
        

driver.quit()
df=pd.DataFrame({'Name':fac_name,'Department':fac_dept,'Title':fac_title,"Url":fac_url})
df.to_csv("northeastern.csv",index=False)