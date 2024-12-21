import requests
import datetime

REGIONS = ["BVBL9180", "BVBL9100", "BVBL9110", "BVBL9120", "BVBL9130", "BVBL9140", "BVBL9150", "BVBL9170", "BVBL9160"]
today = datetime.datetime.now().strftime("%d-%m-%Y")

def check_games(region):
    url = f"https://vblcb.wisseq.eu/VBLCB_WebService/data/MatchesByRegioPeriode?curRegio={region}&dtStart=0&dtEnd=999999999999999999"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    games = []
    for game in data:
        with open("played_games.txt", "r") as f:
            played_games = f.read().splitlines()
            if game["uitslag"] != "" and game["datumString"] == today and not game["guid"] in played_games:
                games.append(game["guid"])
    return games

def get_todays_played_game_guids():
    result = []
    for region in REGIONS:
        games = check_games(region)
        result.extend(games)
    return result

if __name__ == "__main__":
    get_todays_played_game_guids()
