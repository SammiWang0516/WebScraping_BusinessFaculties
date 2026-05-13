#UWashinton __WORKING__

import requests
from bs4 import BeautifulSoup
import pandas as pd

# URL of the faculty directory page
url = "https://foster.uw.edu/faculty-research/academic-departments/dept-marketing-and-international-business/faculty/"

# Send a request to the website
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
response = requests.get(url, headers=headers)

# Check if the request was successful
if response.status_code == 200:
    soup = BeautifulSoup(response.text, "html.parser")
    faculty_data = []
    
    # Find all faculty blocks
    faculty_blocks = soup.find_all("div", class_="col span_12_of_12 slide pop")
    
    for faculty in faculty_blocks:
        name_tag = faculty.find("h2", class_="entry-title")
        title_tag = faculty.find("h3", class_="entry-title job-title dynamic-job-title")
        
        
        
        
        # Extract data
        name = name_tag.text.strip() if name_tag else ""
        title = title_tag.text.strip() if title_tag else ""
        
        
        faculty_data.append({
            "Name": name,
            "Title": title,
            
        })
    
    # Convert to DataFrame
    df = pd.DataFrame(faculty_data)
    
    # Save to Excel
    df.to_excel("foster_faculty_data.xlsx", index=False)
    print("Faculty data has been successfully scraped and saved to 'foster_faculty_data.xlsx'")

else:
    print(f"Failed to retrieve the webpage. Status code: {response.status_code}")