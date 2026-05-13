import requests
import bs4
import pandas as pd
fac_name=[]
fac_title=[]
fac_depts=[]

urls='https://carey.jhu.edu/faculty/faculty-directory'
response=requests.get(urls)
soup=bs4.BeautifulSoup(response.text,'html.parser')
names=soup.find_all('div',{'class':'card fne-card'})

for n in names:
    fac_name.append(n.find_all('h3')[0].text)
    fac_title.append(n.find_all('div',{'class':"field field--name-field-faculty-honorific field--type-string field--label-hidden field__item"})[0].text)
    try:
        fac_depts.append(str(n.find_all('div',{'class':"field field--name-field-faculty-discipline field--type-entity-reference faculty-table"})[0].text))
    except:
        fac_depts.append('')

for i in range(1,13):
    urls=f'https://carey.jhu.edu/faculty/faculty-directory?page={i}'
    response=requests.get(urls)
    soup=bs4.BeautifulSoup(response.text,'html.parser')
    names=soup.find_all('div',{'class':'card fne-card'})

    for n in names:
        fac_name.append(n.find_all('h3')[0].text)
        try:
            fac_title.append(n.find_all('div',{'class':"field field--name-field-faculty-honorific field--type-string field--label-hidden field__item"})[0].text)
        except:
            fac_title.append('')
        try:
            fac_depts.append(str(n.find_all('div',{'class':"field field--name-field-faculty-discipline field--type-entity-reference faculty-table"})[0].text))
        except:
            fac_depts.append('')

df=pd.DataFrame({'Name':fac_name,'Title':fac_title,'Department':fac_depts})
df['Department']=df['Department'].str.replace('\n','; ')
df.to_csv('johnhopkin.csv',index=False)