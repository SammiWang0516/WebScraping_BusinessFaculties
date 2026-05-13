from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd

chrome_options = Options()
chrome_options.add_experimental_option("detach", True)
chrome_options.binary_location = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"  # Update this path if needed
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

urls=[]
exp=[]

url='https://business.cornell.edu/faculty-research/'
driver.get(url)
wait = WebDriverWait(driver, 15)
w=wait.until(EC.presence_of_element_located((By.XPATH, '//div[contains(@class,"g-col") and @data-index="1"]')))
tags=w.find_elements(By.XPATH,'.//li/a')
for t in tags:
    urls.append(t.get_attribute('href'))
    exp.append(t.text)

fac_name=[]
fac_url=[]
fac_type=[]
fac_dept=[]

type=['Regular','Emeriti and Affiliated']
for i,web in enumerate(urls):
    # Specify Chrome binary path if necessary
    driver.get(web)
        
    # Wait for the elements to load
    wait = WebDriverWait(driver, 15)  # Wait up to 15 seconds

    fac_all=wait.until(EC.presence_of_all_elements_located((By.XPATH, '//ul[contains(@class,"faculty--columns")]')))
    for j,typ in enumerate(type):
        facs=fac_all[j].find_elements(By.XPATH,'.//li')
        for f in facs:
            fac_name.append(f.text)
            fac_dept.append(exp[i].replace("%20"," "))
            fac_type.append(typ)
            fac_url.append(f.find_element(By.XPATH,'.//a').get_attribute('href'))
    time.sleep(2)

df=pd.DataFrame({'Name':fac_name,'Department':fac_dept,'Type':fac_type,'URL':fac_url})
titles=[]
for u in fac_url:
    driver.get(u)
    tit=driver.find_element(By.XPATH,'//ul[@class="faculty-profile__list"]')
    titles.append(tit.text.replace('\n','; '))
    time.sleep(1)

driver.quit()
df['Title']=pd.Series(titles)
df.to_csv('cornell_allnames.csv',index=False)
