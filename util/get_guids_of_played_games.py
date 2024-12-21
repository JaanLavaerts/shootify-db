import requests

REGIONS = ["BVBL9180", "BVBL9100", "BVBL9110", "BVBL9120", "BVBL9130", "BVBL9140", "BVBL9150", "BVBL9170", "BVBL9160"]

def check_games(region):
    url = f"https://vblcb.wisseq.eu/VBLCB_WebService/data/MatchesByRegioPeriode?curRegio={region}&dtStart=0&dtEnd=999999999999999999"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    for game in data:
        if game["uitslag"] != "":
            print(game["guid"])



if __name__ == "__main__":
    for region in REGIONS:
        check_games(region)