#This is for Faculty list at UPenn. Each of the department url has to be re-entered and all list grabbed.  _WORKING_ 
#Each university will require to update urls and alter the field code depending on the university website and its layout
# __WORKING__ 


import requests
from bs4 import BeautifulSoup
import csv

# URL of the faculty listing page
url = "https://statistics.wharton.upenn.edu/faculty/faculty-list/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}

# Send request and parse the page
response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, "html.parser")

# Find all faculty list items
faculty_list = []

for li in soup.find_all('li', class_='wdp_listing-row'):
    name_tag = li.find('strong')
    email_tag = li.find('a', class_='wdp_listing-email-button')
    
    if name_tag:
        name = name_tag.text.strip()
    else:
        name = "N/A"

    title = li.get_text(separator=" ").split(",", 1)[1].split("mailto")[0].strip() if "," in li.get_text() else "N/A"

    email = email_tag['href'].replace('mailto:', '') if email_tag else "N/A"

    faculty_list.append([name, title, email])

# Save data to a CSV file
csv_filename = "wharton_faculty.csv"
with open(csv_filename, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["Name", "Title", "Email"])
    writer.writerows(faculty_list)

print(f"Scraped {len(faculty_list)} faculty members. Data saved to {csv_filename}")