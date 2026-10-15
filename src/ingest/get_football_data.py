import os
import requests
import json
from dotenv import load_dotenv
import sys
from pathlib import Path
from datetime import datetime
import time

load_dotenv()  # Used to read API key from the .env file

API_KEY = os.getenv("FOOTBALL_DATA_API_KEY")  # Assigning API key to the API_KEY constant
if not API_KEY:  # Checking if API key is found, if not it exits the program with error message
    sys.exit("Couldn't load API key!")

#  Creating variables for 2 endpoints
PL_matches_endpoint = "https://api.football-data.org/v4/competitions/PL/matches"
teams_endpoint = "https://api.football-data.org/v4/competitions/PL/teams"

#  Headers and parameters for the requests to the endpoints
headers = {"X-Auth-Token": API_KEY}
params = {"season": 2025}
timeout = 5
max_retries = 3

def fetch(url: str, name: str):
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, headers = headers, params = params, timeout = timeout)
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as error:
            print(f"{name} requests error: {error} (attempt {attempt} / {max_retries})")
            time.sleep(5)
            continue
        except requests.exceptions.RequestException as error:
            sys.exit(f"{name} request failed: {error}")

        if response.status_code == 200:
            return response

        if response.status_code == 429:
            wait = int(response.headers.get("X-RequestCounter-Reset", 60))
            print(f"{name} request rate limited, waiting {wait}s (attempt {attempt} / {max_retries})")
            time.sleep(wait)
            continue

        if response.status_code >= 500:
            print(f"{name} request got server error {response.status_code} (attempt {attempt} / {max_retries})")
            time.sleep(5)
            continue

        sys.exit(f"{name} request failed with status {response.status_code}: {response.text}")

    sys.exit(f"{name} request failed after {max_retries} attempts")

PL_matches_response = fetch(PL_matches_endpoint, "matches")
teams_response = fetch(teams_endpoint, "teams")


#  Creating paths to store the raw data from both endpoints, also handling if they exist prior to this script
football_raw_data_path = Path("data/raw/football_data")
matches_path = football_raw_data_path / "matches"
teams_path = football_raw_data_path / "teams"
matches_path.mkdir(parents = True, exist_ok = True)
teams_path.mkdir(parents = True, exist_ok = True)

# Creating time stamp for file formatting
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

# Function that creates json files
def write_json(endpoint_param: str):
    if endpoint_param == "matches":
        json_file = matches_path / f"matches_PL_season_2025-2026_time{timestamp}.json"
        with open(json_file, "w", encoding="utf-8") as j:
            json.dump(PL_matches_response.json(), j, indent = 2)
    elif endpoint_param == "teams":
        json_file = teams_path / f"teams_PL_season_2025-2026_time{timestamp}.json"
        with open(json_file, "w", encoding="utf-8") as j:
            json.dump(teams_response.json(), j, indent = 2)

write_json("matches")
write_json("teams")