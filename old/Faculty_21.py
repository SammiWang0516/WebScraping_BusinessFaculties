#UCLA __WORKING__

import requests
import pandas as pd
from bs4 import BeautifulSoup

# URL of the faculty page
url = "https://www.anderson.ucla.edu/faculty-and-research/strategy/faculty"

# Send a GET request
response = requests.get(url)
soup = BeautifulSoup(response.text, "html.parser")

# Find all faculty containers
faculty_containers = soup.find_all("div", class_="block-container group-list container")
additional_containers = soup.find_all("div", class_="block block-container block--card-carousel block--_04844 inline-block inline-block--card-carousel card-carousel--columns-_ card-carousel--bio-card align-center")

faculty_data = []

# Extract data from first set of containers
for container in faculty_containers:
    faculty_list = container.find_all("li", class_="col-12 col-md-6 col-lg-3 mb-4 views-row")
    for faculty in faculty_list:
        card_body = faculty.find("article", class_="card-body")
        if card_body:
            name_tag = card_body.find("header", class_="profile-name")
            name = name_tag.get_text(strip=True) if name_tag else "Unknown"
            title_tags = card_body.find_all("div", class_="person__field-display-title")
            titles = [t.get_text(strip=True) for t in title_tags]
            for title in titles:
                faculty_data.append([name, title])

# Extract data from additional faculty containers
for container in additional_containers:
    faculty_list = container.find_all("div", class_="col-12 col-md-6 col-lg-3 mb-4")
    for faculty in faculty_list:
        card_body = faculty.find("article", class_="card-body")
        if card_body:
            name_tag = card_body.find("header", class_="profile-name")
            name = name_tag.get_text(strip=True) if name_tag else "Unknown"
            title_tag = card_body.find("div", class_="bio-card__field-text field-name-field-text field-type-text-long")
            titles = title_tag.get_text(strip=True) if title_tag else "Unknown"
            faculty_data.append([name, titles])

# Save to CSV
csv_filename = "ucla_anderson_faculty.csv"
df = pd.DataFrame(faculty_data, columns=["Name", "Title"])
df.to_csv(csv_filename, index=False)

print(f"Data successfully saved to {csv_filename}")
