import requests
from parse import parse_events
from write_to_postgres import write_to_postgres
from write_to_sqlite import write_to_sqlite
import os
from dotenv import load_dotenv
import requests
import datetime

AUTH_HEADER = "Basic YmFza2V0amFhbkBnbWFpbC5jb206YmFza2V0MjM6QjA5QjBFNDAtMTE2OC00RD8hCLUIzQ0QtOTI8MUVDMzdCMjg3"

req_headers = {
    "Authorization": AUTH_HEADER,
    "Content-Type": "application/json; charset=UTF-8",
}

def fetch_game_details(guid):
    req = requests.get("https://vblcb.wisseq.eu/VBLCB_WebService/data/MatchByWedGuid?issguid=" + guid)
    return req.json()[0]["doc"]

def fetch_game_players(guid):
    req_body = {
        "AuthHeader": AUTH_HEADER,
        "WQVer": "v.5b",
        "CRUD": "R",
        "RelNr": "v.5b",
        "WedGUID": guid
    }
    response = requests.put("https://vblcb.wisseq.eu/VBLCB_WebService/data/DwfDeelByWedGuid", headers=req_headers, json=req_body)
    response.raise_for_status()
    data = response.json()
    return data

def fetch_game_events(guid):
    req_body = {
        "AuthHeader": AUTH_HEADER,
        "WQVer": "v.5b",
        "CRUD": "R",
        "RelNr": "v.5b",
        "WedGUID": guid
    }
    response = requests.put("https://vblcb.wisseq.eu/VBLCB_WebService/data/DwfVgngByWedGuid", headers=req_headers, json=req_body)
    response.raise_for_status()
    data = response.json()
    events = data["GebNis"]

    return events


REGIONS = ["BVBL9180", "BVBL9100", "BVBL9110", "BVBL9120", "BVBL9130", "BVBL9140", "BVBL9150", "BVBL9170", "BVBL9160"]
today = datetime.datetime.now().strftime("%d-%m-%Y")

def check_games(region):
    url = f"https://vblcb.wisseq.eu/VBLCB_WebService/data/MatchesByRegioPeriode?curRegio={region}&dtStart=0&dtEnd=999999999999999999"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    games = []
    for game in data:
        with open("./src/played_games.txt", "r") as f:
            played_games = f.read().splitlines()
            if game["uitslag"] != "" and game["datumString"] == today and not game["guid"] in played_games:
                games.append(game["guid"])
    return games

def get_todays_played_game_guids():
    result = []
    for region in REGIONS:
        games = check_games(region)
        result.extend(games)

    if len(result) == 0:
        with open("./src/error_games.txt", "a") as f:
            f.write("No games played yet on " + today + "\n")
    return result

if __name__ == "__main__":
        load_dotenv()

        db_config = {
            "dbname": os.getenv("DB_NAME"),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
            "host": os.getenv("DB_HOST"),
            "port": os.getenv("DB_PORT")
        }

        guids = get_todays_played_game_guids()
        for guid in guids:
            try:
                game_details = fetch_game_details(guid)
                game_players = fetch_game_players(guid)
                game_events = parse_events(fetch_game_events(guid))

                write_to_postgres(game_players, game_events, game_details, db_config)

                with open("./src/played_games.txt", "a") as f:
                    f.write(guid + "\n")
            except Exception as e:
                print(f"Error processing GUID {guid}: {e}")
                with open("./src/error_games.txt", "a") as error_file:
                    error_file.write(guid + "\n")
                continue
            