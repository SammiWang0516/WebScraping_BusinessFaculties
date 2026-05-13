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

#Use mod url with all faculty types clicked
web='https://mendoza.nd.edu/mendoza-directory/?employeetype=Faculty&facultytype=ATF,CF,EF,RF,TF,TTT,V&employeetype=Faculty'

chrome_options = Options()
chrome_options.add_experimental_option("detach", True)
chrome_options.binary_location = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"  # Update this path if needed

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)
driver.get(web)

wait = WebDriverWait(driver, 20)  
select_element = wait.until(EC.presence_of_element_located((By.XPATH, '//select[@class="dept-select"]')))
select = Select(select_element)
optiontxt = [option.text for option in select.options[1:]] 

fac_name=[]
fac_dept=[]
fac_title=[]
fac_email=[]

for option in optiontxt:
    select_element = wait.until(EC.presence_of_element_located((By.XPATH, '//select[@class="dept-select"]')))
    select = Select(select_element)
    select.select_by_visible_text(option)
    time.sleep(2)
    elems=wait.until(EC.presence_of_all_elements_located((By.XPATH, '//div[@class="directory-content"]')))
    for e in elems:
        fac_name.append(e.find_element(By.XPATH,'.//a[@class="a-profile"]').text)
        fac_dept.append(option)
        try:
            fac_title.append(e.text.split('\n')[1])
        except:
            fac_title.append("")
        try:
            fac_email.append(e.text.split('\n')[3])
        except:
            fac_email.append("")
       
driver.quit()
df=pd.DataFrame({'Name':fac_name,'Department':fac_dept,'Title':fac_title,'Email':fac_email})
df.to_csv("notredame.csv",index=False)
#Total 227 records expected but filtering by dept returns 222