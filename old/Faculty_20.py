#Pennsylvania State University at State College (Penn State) (Smeal College of Business) __NOT WORKING__


import requests
import pandas as pd
from bs4 import BeautifulSoup

# URL of the faculty page
url = "https://www.smeal.psu.edu/accounting/acctg/people/faculty/"

# Send a GET request
response = requests.get(url)
soup = BeautifulSoup(response.text, "html.parser")

# Find all rows <tr> that contain height attributes (faculty entries)
rows = soup.find_all("tr", style=True)

# Store faculty data
faculty_data = []

for row in rows:
    cells = row.find_all("td")
    
    # Ensure row has enough columns
    if len(cells) < 2:
        continue  # Skip invalid rows

    # Extract name (which is usually inside <p> or <a>)
    name_cell = cells[0]
    name = name_cell.get_text(strip=True)

    # Extract titles (some faculty have multiple titles inside <p>)
    title_cell = cells[1]
    titles = [p.get_text(strip=True) for p in title_cell.find_all("p") if p.get_text(strip=True)]

    # Append each title separately
    for title in titles:
        faculty_data.append([name, title])

# Save to CSV
csv_filename = "psu_smeal_faculty_fixed.csv"
df = pd.DataFrame(faculty_data, columns=["Name", "Title"])
df.to_csv(csv_filename, index=False)

print(f"Data successfully saved to {csv_filename}")