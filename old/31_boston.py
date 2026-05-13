from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd

web = 'https://www.bu.edu/questrom/faculty/faculty-directory/'

chrome_options = Options()
chrome_options.add_experimental_option("detach", True)
chrome_options.binary_location = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"  # Update this path if needed

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)
driver.get(web)

fac_name=[]
fac_dept=[]
fac_url=[]
fac_title=[]

wait = WebDriverWait(driver, 20)  
options = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//li[@class="directory__filter-option"]')))
depts = [driver.execute_script("return arguments[0].textContent;", t) for t in wait.until(EC.presence_of_all_elements_located((By.XPATH, '//li/span')))]
for option,d in zip(options,depts):
    driver.execute_script("arguments[0].click();", option)
    time.sleep(4)
    facs=wait.until(EC.presence_of_all_elements_located((By.XPATH, '//li[@class="directory__card"]')))
    for fac in facs:
        fac_name.append(fac.find_element(By.XPATH,'.//h2[@class="directory__name"]').text)
        fac_dept.append(d)
        fac_url.append(fac.find_element(By.XPATH,'.//a').get_attribute('href'))
        fac_title.append("; ".join([e.text for e in fac.find_elements(By.XPATH,'.//p[@class="directory__role"]')]))

    clr=wait.until(EC.presence_of_element_located((By.XPATH, '//button[@class="directory__clear"]')))
    driver.execute_script("arguments[0].click();", clr)
    time.sleep(1)

driver.quit()
df=pd.DataFrame({'Name':fac_name,'Department':fac_dept,'Title':fac_title,'URL':fac_url})
df.to_csv('boston.csv',index=False)