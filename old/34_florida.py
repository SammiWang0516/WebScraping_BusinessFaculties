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

web='https://warrington.ufl.edu/directory/profiles/?faculty=true'


chrome_options = Options()
chrome_options.add_experimental_option("detach", True)
chrome_options.binary_location = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"  # Update this path if needed

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)
driver.get(web)

wait = WebDriverWait(driver, 10)  
select_element = wait.until(EC.presence_of_element_located((By.XPATH, '//select[@class="fg-line form-control input-ous"]')))
select = Select(select_element)
optiontxt = [option.text for option in select.options[1:]] 

fac_name=[]
fac_dept=[]
fac_title=[]
fac_email=[]
fac_phone=[]
fac_expertise=[]

for option in optiontxt:
    select_element = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//select[@class="fg-line form-control input-ous"]')))[0]
    select = Select(select_element)
    select.select_by_visible_text(option)
    time.sleep(2)
    elems=wait.until(EC.presence_of_all_elements_located((By.XPATH, '//div[contains(@class,"card person")]')))
    for e in elems:
        if e.is_displayed():
            fac_name.append(e.find_element(By.XPATH,'.//div[contains(@class,"card-header")]').text)
            fac_dept.append(option)
            body=e.find_elements(By.XPATH,'.//p[@class="mb-1"]')
            try:
                fac_title.append(body[0].text)
            except:
                fac_title.append("")
            try:
                fac_email.append(body[1].find_element(By.XPATH,'.//a').get_attribute('href'))
            except:
                fac_email.append("")
            try:
                fac_phone.append(e.find_element(By.XPATH,'.//p[@class="mb-05"]').text)
            except:
                fac_phone.append("")
            try:
                fac_expertise.append(e.find_element(By.XPATH,'.//ul').text)
            except:
                fac_expertise.append("")

driver.quit()
df=pd.DataFrame({'Name':fac_name,'Department':fac_dept,'Title':fac_title,'Expertise':fac_expertise,'Email':fac_email,'Phone':fac_phone})
df.Title=df.Title.apply(lambda x: x.replace('\n','; '))
df.to_csv("florida_warrington.csv",index=False)