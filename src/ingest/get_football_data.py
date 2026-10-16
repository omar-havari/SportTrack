import os
import requests
import json
from dotenv import load_dotenv
import sys
from pathlib import Path
from datetime import datetime
import time
import logging
from log_setup import setup_logging

load_dotenv()  # Used to read API key from the .env file
setup_logging()

API_KEY = os.getenv("FOOTBALL_DATA_API_KEY")  # Assigning API key to the API_KEY constant
if not API_KEY:  # Checking if API key is found, if not it exits the program with error message
    logging.error("Couldn't load API key")
    sys.exit(1)



#  Creating variables for 2 endpoints
PL_matches_endpoint = "https://api.football-data.org/v4/competitions/PL/matches"
teams_endpoint = "https://api.football-data.org/v4/competitions/PL/teams"

#  Headers and parameters for the requests to the endpoints
headers = {"X-Auth-Token": API_KEY}
params = {"season": 2025}
timeout = 5
max_retries = 3
expected_teams = 20
expected_matches = 380

def fetch(url: str, name: str):
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, headers = headers, params = params, timeout = timeout)
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as error:
            logging.warning(f"{name} requests error: {error} (attempt {attempt} / {max_retries})")
            time.sleep(5)
            continue
        except requests.exceptions.RequestException as error:
            logging.error(f"{name} request failed: {error}")
            sys.exit(1)

        if response.status_code == 200:
            return response

        if response.status_code == 429:
            wait = int(response.headers.get("X-RequestCounter-Reset", 60))
            logging.warning(f"{name} request rate limited, waiting {wait}s (attempt {attempt} / {max_retries})")
            time.sleep(wait)
            continue

        if response.status_code >= 500:
            logging.warning(f"{name} request got server error {response.status_code} (attempt {attempt} / {max_retries})")
            time.sleep(5)
            continue

        logging.error(f"{name} request failed with status {response.status_code}: {response.text}")
        sys.exit(1)

    logging.error(f"{name} request failed after {max_retries} attempts")
    sys.exit(1)

PL_matches_response = fetch(PL_matches_endpoint, "matches")
teams_response = fetch(teams_endpoint, "teams")

matches_data = PL_matches_response.json()
teams_data = teams_response.json()

matches_count = len(matches_data.get("matches", []))
teams_count = len(teams_data.get("teams", []))
logging.info(f"matches: received {matches_count} records (API reports {matches_data.get('resultSet', {}).get('count')})")
logging.info(f"teams: received {teams_count} records (API reports {teams_data.get('count')})")

if matches_count != expected_matches:
    logging.warning(f"matches: expected {expected_matches}, got {matches_count}")
if teams_count != expected_teams:
    logging.warning(f"teams: expected {expected_teams}, got {teams_count}")


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
            json.dump(matches_data, j, indent = 2)
        logging.info(f"Saved {json_file}")
    elif endpoint_param == "teams":
        json_file = teams_path / f"teams_PL_season_2025-2026_time{timestamp}.json"
        with open(json_file, "w", encoding="utf-8") as j:
            json.dump(teams_data, j, indent = 2)
        logging.info(f"Saved {json_file}")

write_json("matches")
write_json("teams")