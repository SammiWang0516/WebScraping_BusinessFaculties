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

#Use modified URL with all - emeritus, visiting etc type faculty clicked- Better than manual selection
web='https://broad.msu.edu/directory/?q=&expertise=0&program=0&department=0&employment%5B%5D=1&employment%5B%5D=2&employment%5B%5D=5&employment%5B%5D=7&employment%5B%5D=8&Submit=Search'

chrome_options = Options()
chrome_options.add_experimental_option("detach", True)
chrome_options.binary_location = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"  # Update this path if needed

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)
driver.get(web)

wait = WebDriverWait(driver, 20)  
select_element = wait.until(EC.presence_of_element_located((By.XPATH, '//select[@id="bps-dept"]')))
select = Select(select_element)
optiontxt = [driver.execute_script("return arguments[0].textContent;", option) for option in select.options[1:]] 

fac_name=[]
fac_dept=[]
fac_title=[]
fac_email=[]
fac_ph=[]

for o in optiontxt: #Skip 1, indexed from 1 not zero
    cl=wait.until(EC.presence_of_element_located((By.XPATH, '//a[@class="accordion-title"]'))).click()
    select_element = wait.until(EC.presence_of_element_located((By.XPATH, '//select[@id="bps-dept"]')))
    select = Select(select_element)
    select.select_by_visible_text(o)
    sbmt = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@value="Search"]')))
    driver.execute_script("arguments[0].click();", sbmt)
    time.sleep(2)
    while True:
        try:
            elems=wait.until(EC.presence_of_all_elements_located((By.XPATH, '//div[@class="profile-listing cell"]')))
            for e in elems:
                fac_name.append(e.find_element(By.XPATH,'.//h2').text)
                fac_dept.append(o)
                try:
                    fac_title.append(e.find_element(By.XPATH,'.//div[contains(@class,"titles-bio")]').text)
                except:
                    fac_title.append("")
                try:
                    fac_email.append(e.find_element(By.XPATH,'.//div[contains(@class,"directory-email")]').text)
                except:
                    fac_email.append("")
                try:
                    fac_ph.append(e.find_element(By.XPATH,'.//div[contains(@class,"directory-phone")]').text)
                except:
                    fac_ph.append("")
           
            nxtpg=wait.until(EC.presence_of_element_located((By.XPATH, '//li[contains(@class,"pager_tail page-item")]/a')))
            driver.execute_script("arguments[0].click();", nxtpg)
            time.sleep(2)
        except:
            time.sleep(1)
            break

driver.quit()
df=pd.DataFrame({'Name':fac_name,'Department':fac_dept,'Title':fac_title,'Phone':fac_ph,'Email':fac_email})
df.Title=df.Title.apply(lambda x: x.replace('\n','; '))
df.to_csv("michiganstate.csv",index=False)