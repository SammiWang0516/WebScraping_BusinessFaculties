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

urls=['https://sc.edu/study/colleges_schools/moore/study/accounting/our_people/index.php',
      'https://sc.edu/study/colleges_schools/moore/study/economics/our_people/index.php',
      'https://sc.edu/study/colleges_schools/moore/study/management/our_people/index.php',
      'https://sc.edu/study/colleges_schools/moore/study/finance/our_people/index.php',
      'https://sc.edu/study/colleges_schools/moore/study/international_business/our_people/index.php',
      'https://sc.edu/study/colleges_schools/moore/study/marketing/our_people/index.php',
      'https://sc.edu/study/colleges_schools/moore/study/management_science/our_people/index.php']

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
fac_ph=[]
em_name=[]
em_dept=[]
em_alldetails=[]
for web in urls:
    driver.get(web)
    elems=wait.until(EC.presence_of_all_elements_located((By.XPATH, '//div[@class="blurb"]')))
    for e in elems:
        fac_name.append(e.find_element(By.XPATH,'.//a').text)
        fac_dept.append(web.split('/')[-3])
        try:
            fac_title.append(e.find_element(By.XPATH,'.//p[1]').text)
        except:
            fac_title.append("")
        try:
            fac_email.append(e.find_element(By.XPATH,'.//p[2]').text)
        except:
            fac_email.append("")
        try:
            fac_ph.append(e.find_element(By.XPATH,'.//p[3]').text)
        except:
            fac_ph.append("")
    emeritus=wait.until(EC.presence_of_all_elements_located((By.XPATH, '//p[@class="sub-text"]')))
    for e in emeritus:
        e_det=e.text.split('\n')
        em_name.append(e_det[0])
        em_dept.append(web.split('/')[-3])
        em_alldetails.append(e.text)
            
driver.quit()
df=pd.DataFrame({'Name':fac_name,'Department':fac_dept,'Title':fac_title,'Phone':fac_ph,'Email':fac_email})
df['Title']=df['Title'].str.replace('\n','; ')
df.to_csv("southcarolina_fix_regular.csv",index=False)
df2=pd.DataFrame({'Name':em_name,'Department':em_dept,'AllDetails':em_alldetails})
df2['AllDetails']=df2['AllDetails'].str.replace('\n','; ')
df2.to_csv('southcarolina_fix_emeritus.csv',index=False)