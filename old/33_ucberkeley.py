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

web = 'https://haas.berkeley.edu/faculty/'

chrome_options = Options()
chrome_options.add_experimental_option("detach", True)
chrome_options.binary_location = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"  # Update this path if needed

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)
driver.get(web)

fac_name=[]
fac_about=[]
fac_dept=[]
fac_url=[]
fac_title=[]

wait = WebDriverWait(driver, 20)  
select_element = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//select[@id="faculty-areas"]')))[0]
select = Select(select_element)
optiontxt = [option.text for option in select.options[1:]] 

for option in optiontxt:
    select_element = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//select[@id="faculty-areas"]')))[0]
    select = Select(select_element)
    select.select_by_visible_text(option)
    time.sleep(4)
    while True:
        try:
            lm=wait.until(EC.presence_of_element_located((By.XPATH,'//a[contains(@class,"view-more")]'))).click()
            time.sleep(4)
        except:
            time.sleep(4)
            break
    facs=wait.until(EC.presence_of_all_elements_located((By.XPATH, '//a[@class="wrap-link grid-block"]')))
    for fac in facs:
        fac_name.append(fac.find_element(By.XPATH,'.//h2').text)
        fac_dept.append(option)
        fac_url.append(fac.get_attribute('href'))
        try:
            fac_about.append(fac.find_element(By.XPATH,'.//p').text)
            fac_title.append(fac.find_element(By.XPATH,'.//strong').text)
        except:
            fac_about.append("")
            fac_title.append("")

driver.quit()
df=pd.DataFrame({'Name':fac_name,'Department':fac_dept,'Title':fac_title,'About':fac_about,'URL':fac_url})
df.to_csv('berkeley_haas.csv',index=False)