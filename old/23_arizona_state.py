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

web = ['https://wpcarey.asu.edu/people/departments/accountancy',
       'https://wpcarey.asu.edu/people/departments/morrison-agribusiness',
       'https://wpcarey.asu.edu/people/departments/economics',
       'https://wpcarey.asu.edu/people/departments/finance',
       'https://wpcarey.asu.edu/people/departments/information-systems',
       'https://wpcarey.asu.edu/people/departments/management-entrepreneurship',
       'https://wpcarey.asu.edu/people/directory/marketing',
       'https://wpcarey.asu.edu/people/departments/master-real-estate-development',
       'https://wpcarey.asu.edu/people/departments/supply-chain-management',
       'https://wpcarey.asu.edu/people/departments/school-of-technology']

chrome_options = Options()
chrome_options.add_experimental_option("detach", True)
chrome_options.binary_location = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"  # Update this path if needed

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)


fac_name=[]
fac_dept=[]
fac_scrape_url_dept=[]
fac_url=[]
fac_title=[]
fac_email=[]

wait = WebDriverWait(driver, 20)

for w in web:
    driver.get(w)
    while True:
        try:
            time.sleep(2)
            facs=wait.until(EC.presence_of_all_elements_located((By.XPATH, '//div[@class="person"]')))
            for fac in facs:
                fac_name.append(fac.find_element(By.XPATH,'.//a').text)
                fac_scrape_url_dept.append(w.split('/')[-1])
                fac_url.append(fac.find_element(By.XPATH,'.//a').get_attribute('href'))
                try:
                    fac_dept.append(fac.find_element(By.XPATH,'.//div[@class="person-profession"]/span').text)
                    fac_title.append(fac.find_element(By.XPATH,'.//div[@class="person-profession"]/h4').text)
                except:
                    fac_dept.append("")
                    fac_title.append("")
                try:
                    fac_email.append(fac.find_element(By.XPATH,'.//ul[@class="person-contact-info"]/li/a').text)
                except:
                    fac_email.append("")
                
            nxtpg=wait.until(EC.presence_of_element_located((By.XPATH, '//li[@class="page-item"]/button[@aria-label="Next Page"]')))
            driver.execute_script("arguments[0].click();", nxtpg)
            time.sleep(5)
        except:
            time.sleep(1)
            break

driver.quit()
df=pd.DataFrame({'Name':fac_name,'Scraped from Dept':fac_scrape_url_dept,'Department':fac_dept,'Title':fac_title,'URL':fac_url,'Email':fac_email})
df.to_csv('arizonastate.csv',index=False)