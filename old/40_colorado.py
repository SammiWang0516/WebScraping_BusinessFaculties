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

urls=['https://www.colorado.edu/business/faculty-research/faculty-directory/accounting-faculty',
      'https://www.colorado.edu/business/faculty-research/directory/finance-faculty',
      'https://www.colorado.edu/business/faculty-research/faculty-directory/marketing-faculty',
      'https://www.colorado.edu/business/faculty-research/faculty-directory/organizational-leadership-and-information-analytics-faculty',
      'https://www.colorado.edu/business/faculty-research/directory/professional-effectiveness-faculty',
      'https://www.colorado.edu/business/faculty-research/faculty-directory/social-responsibility-and-sustainability',
      'https://www.colorado.edu/business/faculty-research/directory/strategy-entrepreneurship-and-operations-faculty',
      'https://www.colorado.edu/business/faculty-research/faculty-directory/emeritus-faculty-members']
chrome_options = Options()
chrome_options.add_experimental_option("detach", True)
chrome_options.binary_location = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"  # Update this path if needed

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)


fac_name=[]
fac_title=[]
fac_depts=[]

wait = WebDriverWait(driver, 20)

for i in urls:
    time.sleep(5)
    driver.get(i)
    people=wait.until(EC.presence_of_all_elements_located((By.XPATH,'//div[@class="col-sm-12 col-md-6 col-lg-4"]')))

    for p in people:
        fac_name.append(p.find_element(By.XPATH,'.//h2').text)
        fac_title.append(p.find_element(By.XPATH,'.//span[contains(@class,"title-grid")]').text)
        fac_depts.append(p.find_element(By.XPATH,'.//span[contains(@class,"departments-grid")]').text)

driver.quit()

df=pd.DataFrame({'Name':fac_name,'Title':fac_title,'Departments':fac_depts})
df['Departments']=df['Departments'].str.replace('\u2022','; ')
df.to_csv("colorado_leeds.csv",index=False)