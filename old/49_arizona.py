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

web = 'https://eller.arizona.edu/directory'

# Specify Chrome binary path if necessary
chrome_options = Options()
chrome_options.add_experimental_option("detach", True)
chrome_options.binary_location = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"  # Update this path if needed

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)
driver.get(web)

wait = WebDriverWait(driver, 5)  

# Click the "Faculty" option in the first dropdown
driver.find_element(By.XPATH, '//select[contains(@class,"form-select")]/option[text()="Faculty"]').click()
name=[]
info=[]
contact=[]
depts=[]
try:
    # Re-locate the second dropdown and its options
    select_element = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//select[contains(@class,"form-select")]')))[1]
    select = Select(select_element)
    optiontxt = [option.text for option in select.options[1:]]  # Skip the first option (e.g., "Select")

    for option in optiontxt:
        # Re-locate the dropdown and select the current option
        select_element = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//select[contains(@class,"form-select")]')))[1]
        select = Select(select_element)
        select.select_by_visible_text(option)
        # Click the "Apply" button
        app = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[@value="Apply"]')))
        driver.execute_script("arguments[0].click();", app)
        time.sleep(5)
        #Scrape
        try:
            cards = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//div[contains(@class,"card-body")]')))
        except:
            continue
        for card in cards:
            try:
                name.append(card.find_element(By.XPATH, './/h3').text)
                depts.append(option)
            except:
                continue
            try:
                info.append(card.find_element(By.XPATH, './/div[contains(@class,"field field--name")]').text)
            except:
                info.append("")
            try:
                contact.append(card.find_element(By.XPATH, './/div[@class="mt-3"]').text)
            except:
                contact.append("")
        time.sleep(1)

except Exception as e:
    print(f"Error: {e}")

finally:
    driver.quit()
df=pd.DataFrame({
    'Name': name,
    'Department': depts,
    'Title': info,
    'Contact': contact
})
df.Title=df.Title.apply(lambda x: x.replace('\n','; '))
df.to_csv('arizona.csv', index=False)