#Umich Ross __WORKING__

import requests
import csv
from bs4 import BeautifulSoup

# URL of the faculty directory
url = "https://michiganross.umich.edu/faculty-research/directory?department=74&name=&sort_by=sort_a&status=All&page=2"

# Send a request to fetch the webpage
response = requests.get(url)
response.raise_for_status()  # Raise an error if request fails

# Parse the webpage content using BeautifulSoup
soup = BeautifulSoup(response.text, "html.parser")

# Find all faculty members (inside div class="views-row")
faculty_list = soup.find_all("div", class_="views-row")

# List to store extracted faculty data
data = []

# Iterate through each faculty block
for faculty in faculty_list:
    # Extract name
    name_tag = faculty.find("div", class_="h4 grid__teaser__title")
    name = name_tag.get_text(strip=True) if name_tag else "N/A"

    # Extract title(s) (each in a separate field__item div)
    title_container = faculty.find("div", class_="field field--name-field-faculty-title field--type-string field--label-hidden field__items")
    titles = title_container.find_all("div", class_="field__item") if title_container else []

    # Combine multiple titles into a single string
    title_text = ", ".join([title.get_text(strip=True) for title in titles if title.get_text(strip=True)])

    # Append the data as a single row
    data.append([name, title_text])

# Save extracted data into a CSV file
csv_filename = "michigan_ross_faculty_fixed.csv"
with open(csv_filename, "w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["Name", "Title"])  # Write header
    writer.writerows(data)  # Write faculty data rows

print(f"✅ Data successfully saved to {csv_filename}!")