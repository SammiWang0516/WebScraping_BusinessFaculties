import bs4
import requests
import pandas as pd

web='https://www.business.uconn.edu/contact/faculty/'
response = requests.get(web)
soup = bs4.BeautifulSoup(response.text, 'html.parser')

body=soup.find_all('div',{'class':'entry-content'})[0]
urls=[u['href'] for u in body.find_all('a')][1:]
fac_name=[]
fac_title=[]
fac_dept=[]
fac_campus=[]
for web in urls:
    soup=bs4.BeautifulSoup(requests.get(web).text, 'html.parser')
    persons=soup.find_all('div',{'class':'person'})
    for person in persons:
        fac_name.append(person.find('h4').text)
        fac_title.append(person.find('p',{'class':'person-title'}).text)
        fac_dept.append(person.find('p',{'class':'person-department'}).text)
        fac_campus.append(person.find('p',{'class':'person-campus'}).text)

df=pd.DataFrame({'name':fac_name,'title':fac_title,'department':fac_dept,'campus':fac_campus})
df.to_csv('uconn.csv',index=False)