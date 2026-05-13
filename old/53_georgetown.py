import requests
import bs4
import pandas as pd

depts=['accounting-business-law','finance','management','marketing',
       'operations-analytics','strategy-economics-ethics-public-policy']
faculty_name=[]
faculty_title=[]
faculty_dept=[]
faculty_url=[]

for dept in depts:
    url=f'https://msb.georgetown.edu/faculty-research/{dept}'
    response = requests.get(url)
    soup = bs4.BeautifulSoup(response.text, 'html.parser')
    names=soup.find_all('div',{'class':'gu-block gu-cards-card gu-block-profile-card is-style-flush-top'})
    for name in names:
        faculty_name.append(name.find_all('a')[0].text)
        faculty_title.append(name.find_all('p')[-1].text)
        faculty_dept.append(dept)
        faculty_url.append(name.find_all('a')[0]['href'])

df=pd.DataFrame({'Name':faculty_name,'Title':faculty_title,'Department':faculty_dept,'URL':faculty_url})
df.to_csv('georgetown.csv',index=False)
print(len(df),'Extraction Complete')

