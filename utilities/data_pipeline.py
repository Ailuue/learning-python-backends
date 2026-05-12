import pandas as pd
import requests

# 1. Extract: Fetch data from a common public endpoint (Users)
url = "https://jsonplaceholder.typicode.com/users"
response = requests.get(url)

# Ensure the request was successful
if response.status_code == 200:
    data = response.json()  # This returns a list of dictionaries

    # 2. Transform: Load into a pandas DataFrame
    # Nested fields like 'address' or 'company' will remain as dicts in the cells
    df = pd.DataFrame(data)

    # Optional: Flatten nested 'company' data into its own columns
    company_df = pd.json_normalize(df["company"].tolist())
    df = pd.concat([df.drop("company", axis=1), company_df], axis=1)

    # 3. Load: Display the first 5 rows
    print(df.head())
else:
    print(f"Failed to fetch data. Status code: {response.status_code}")
