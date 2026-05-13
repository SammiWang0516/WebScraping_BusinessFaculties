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


web=['https://www.fox.temple.edu/faculty-research/academic-areas/accounting/faculty',
     'https://www.fox.temple.edu/faculty-research/academic-areas/finance/faculty',
     'https://www.fox.temple.edu/faculty-research/academic-areas/management/faculty',
     'https://www.fox.temple.edu/faculty-research/academic-areas/management-information-systems/faculty',
     'https://www.fox.temple.edu/faculty-research/academic-areas/marketing/faculty',
     'https://www.fox.temple.edu/faculty-research/academic-areas/risk-actuarial-science-and-legal-studies/faculty',
     'https://www.fox.temple.edu/faculty-research/academic-areas/statistics-operations-and-data-science/faculty']

chrome_options = Options()
chrome_options.add_experimental_option("detach", True)
chrome_options.binary_location = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"  # Update this path if needed

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

wait = WebDriverWait(driver, 20)  

fac_name=[]
fac_dept=[]
fac_title=[]
fac_email=[]

for w in web:
    driver.get(w)
    time.sleep(4)
    elems=wait.until(EC.presence_of_all_elements_located((By.XPATH, '//li[@class="catalog__item"]')))
    for e in elems:
        fac_name.append(e.find_element(By.XPATH,'.//h2[contains(@class,"title")]').text)
        try:
            fac_dept.append(e.find_element(By.XPATH,'.//p[contains(@class,"position__secondary-label")]').text)
        except:
            fac_dept.append("")
        try:
            fac_title.append(e.find_element(By.XPATH,'.//p[contains(@class,"position__title")]').text)
        except:
            fac_title.append("")
        try:
            eml=e.find_element(By.XPATH,'.//div[@class="content__profile--contact --transition"]/ul/li/p/a')
            fac_email.append(driver.execute_script("return arguments[0].textContent;", eml))
        except:
            fac_email.append("")       

driver.quit()
df=pd.DataFrame({'Name':fac_name,'Department':fac_dept,'Title':fac_title,'Email':fac_email})
df.to_csv("temple_fox_fix.csv",index=False)