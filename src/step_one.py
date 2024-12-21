import requests
from parse import parse_events
from write_to_postgres import write_to_postgres
from write_to_sqlite import write_to_sqlite
import os
from dotenv import load_dotenv

AUTH_HEADER = "Basic YmFza2V0amFhbkBnbWFpbC5jb206YmFza2V0MjM6QjA5QjBFNDAtMTE2OC00RD8hCLUIzQ0QtOTI8MUVDMzdCMjg3"

req_headers = {
    "Authorization": AUTH_HEADER,
    "Content-Type": "application/json; charset=UTF-8",
}

def fetch_game_details(guid):
    req = requests.get("https://vblcb.wisseq.eu/VBLCB_WebService/data/MatchByWedGuid?issguid=" + guid)
    req.raise_for_status()  # Raise an exception for HTTP errors
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


if __name__ == "__main__":
    with open("./src/played_games.txt", "r") as file:
        load_dotenv()

        db_config = {
            "dbname": os.getenv("DB_NAME"),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
            "host": os.getenv("DB_HOST"),
            "port": os.getenv("DB_PORT")
        }

        for line in file:
            guid = line.strip()
            try:
                print(f"Processing GUID: {guid}")
                game_details = fetch_game_details(guid)
                game_players = fetch_game_players(guid)
                game_events = parse_events(fetch_game_events(guid))
                write_to_postgres(game_players, game_events, game_details, db_config)
                print(f"Successfully processed GUID: {guid}")
            except Exception as e:
                print(f"Error processing GUID {guid}: {e}")
                with open("./src/error_games.txt", "a") as error_file:
                    error_file.write(guid + "\n")
                continue
