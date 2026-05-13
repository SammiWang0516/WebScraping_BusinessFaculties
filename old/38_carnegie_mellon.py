import requests
import bs4

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

url = 'https://www.cmu.edu/tepper/faculty-and-research/faculty-by-area/index.html'
response = requests.get(url)
soup = bs4.BeautifulSoup(response.text, 'html.parser')
base = 'https://www.cmu.edu/tepper/faculty-and-research/faculty-by-area/'
urls = [base + u['href'] for u in soup.find_all('a', {'class': 'cta'})]
depts = [" ".join(u.text.split(' ')[:-1]) for u in soup.find_all('a', {'class': 'cta'})]

fac_dept = []
fac_name = []
fac_title = []

for d, u in zip(depts, urls):
    chrome_options = Options()
    chrome_options.add_experimental_option("detach", True)
    chrome_options.binary_location = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"  # Update this path if needed

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get(u)

    # Wait for the page to load
    wait = WebDriverWait(driver, 5)
    while True: #Loop to load all elements by clicking load more
        try:
            lm=wait.until(EC.presence_of_element_located((By.XPATH,'//span[contains(@class,"loadmore align-center")]'))).click()
            time.sleep(2)
        except:
            time.sleep(2)
            break  # Allow initial content to load
    # Locate and scrape the elements
    elems = driver.find_elements(By.XPATH, '//div[contains(@class,"filterable")]')
    for elem in elems:
        name = elem.find_element(By.XPATH, './/h2').text
        title = elem.find_element(By.XPATH, './/h3').text
        fac_name.append(name)
        fac_title.append(title)
        fac_dept.append(d)

    driver.quit()

# Save the data to a CSV file
df = pd.DataFrame({'Name': fac_name, 'Department': fac_dept, 'Title': fac_title})
df.to_csv('cmu_tepper.csv', index=False)