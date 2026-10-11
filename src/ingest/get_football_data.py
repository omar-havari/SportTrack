import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("FOOTBALL_DATA_API_KEY")
url = "https://api.football-data.org/v4/competitions/PL/matches"
headers = {"X-Auth-Token": API_KEY}
params = {"season": 2025}

response = requests.get(url, headers = headers, params = params)
data = response.json()
print(json.dumps(data["matches"][1], indent=2))




# Load the API key from .env
# Request the matches for one competition and season
# Check the request succeeded
# Save the raw response to data/raw/
# Log how many record came back