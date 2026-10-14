import os
import requests
import json
from dotenv import load_dotenv
import sys
from pathlib import Path
from datetime import datetime

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

#  Storing responses in variables
try:
    PL_matches_response = requests.get(PL_matches_endpoint, headers = headers, params = params, timeout = timeout)
    teams_response = requests.get(teams_endpoint, headers = headers, params = params, timeout = timeout)
except requests.exceptions.RequestException as error:
    print(f"There was an error: {error}")
    sys.exit(1)


failed = False

if PL_matches_response.status_code != 200:
    print(f"matches request failed with status {PL_matches_response.status_code}: {PL_matches_response.text}")
    failed = True

if teams_response.status_code != 200:
    print(f"teams request failed with status {teams_response.status_code}: {teams_response.text}")
    failed = True

if failed:
    sys.exit(1)

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