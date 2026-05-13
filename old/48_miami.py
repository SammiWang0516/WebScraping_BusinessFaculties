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


web='https://www.herbert.miami.edu/faculty-research/directory/index.html'

chrome_options = Options()
chrome_options.add_experimental_option("detach", True)
chrome_options.binary_location = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"  # Update this path if needed

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)
driver.get(web)

wait = WebDriverWait(driver, 20)  
select_element = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//div[@class="filter-group Department"]/div[@class="filter-options"]/ul/li')))
optiontxt = [driver.execute_script("return arguments[0].textContent;", option) for option in select_element]
fac_name=[]
fac_dept=[]
fac_title=[]
fac_url=[]

for i in range(len(optiontxt)):
    sel = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//div[@class="filter-group Department"]/div[@class="filter-options"]/ul/li')))[i].find_element(By.XPATH,'.//a')
    driver.execute_script("arguments[0].click();", sel)    
    time.sleep(5)
    while True:
        try:
            elems=wait.until(EC.presence_of_all_elements_located((By.XPATH, '//div[@class="column "]'))) #Note there is a " " space in xpath
            for e in elems:
                fac_name.append(e.find_element(By.XPATH,'.//a/div/h2').text)
                fac_dept.append(optiontxt[i])
                try:
                    fac_title.append(e.find_element(By.XPATH,'.//a/div/div').text)
                except:
                    fac_title.append("")
                try:
                    fac_url.append(e.find_element(By.XPATH,'.//a').get_attribute('href'))
                except:
                    fac_url.append("")
           
            nxtpg=wait.until(EC.presence_of_element_located((By.XPATH, '//li[@class="paging-next"]/a')))
            driver.execute_script("arguments[0].click();", nxtpg)
            time.sleep(5)
        except:
            time.sleep(1)
            driver.execute_script("arguments[0].click();", sel)
            break
        

driver.quit()
df=pd.DataFrame({'Name':fac_name,'Department':fac_dept,'Title':fac_title,"Url":fac_url})
df.Title=df.Title.apply(lambda x: x.replace('\n','; '))
df.to_csv("miami.csv",index=False)