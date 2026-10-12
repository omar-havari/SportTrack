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
matches_endpoint = "https://api.football-data.org/v4/competitions/PL/matches"
teams_endpoint = "https://api.football-data.org/v4/competitions/PL/teams"

#  Headers and parameters for the requests to the endpoints
headers = {"X-Auth-Token": API_KEY}
params = {"season": 2025}

#  Storing responses in variables
matches_response = requests.get(matches_endpoint, headers = headers, params = params)
teams_response = requests.get(teams_endpoint, headers = headers, params = params)


#  Checking if responses aren't valid
if matches_response.status_code != 200 or teams_response.status_code != 200:
    sys.exit("Couldn't establish connection!")

#  Creating paths to store the raw data from both endpoints, also handling if they exist prior to this script
football_raw_data_path = Path("data/raw/football_data")
matches_path = football_raw_data_path / "matches"
teams_path = football_raw_data_path / "teams"
matches_path.mkdir(parents = True, exist_ok = True)
teams_path.mkdir(parents = True, exist_ok = True)
