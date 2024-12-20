from typing import Dict, Optional, Set, List, Union
import re


class PlayerStats:
    def __init__(self):
        self.totalPoints = 0
        self.quarters = {}
        self.onePointers = 0
        self.twoPointers = 0
        self.threePointers = 0
        self.fouls = 0
        self.totalMinutesPlayed = 0
        self.RelGUID = ""
        self.plusMinus = 0

    def to_dict(self):
        return {
            "totalPoints": self.totalPoints,
            "quarters": self.quarters,
            "onePointers": self.onePointers,
            "twoPointers": self.twoPointers,
            "threePointers": self.threePointers,
            "fouls": self.fouls,
            "totalMinutesPlayed": self.totalMinutesPlayed,
            "RelGUID": self.RelGUID,
            "plusMinus": self.plusMinus,
        }


class TeamStats:
    def __init__(self):
        self.players: Dict[str, PlayerStats] = {}
        self.totalPoints = 0

    def to_dict(self):
        return {
            "players": {player_id: player.to_dict() for player_id, player in self.players.items()},
            "totalPoints": self.totalPoints,
        }


class GameStats:
    def __init__(self):
        self.homeTeam = TeamStats()
        self.awayTeam = TeamStats()
        self.teamThuisGUID = ""
        self.teamThuisNaam = ""
        self.teamUitGUID = ""
        self.teamUitNaam = ""
        self.datumString = ""
        self.pouleGUID = ""
        self.pouleNaam = ""
        self.gespeeld = ""
        self.uitslag = ""
        self.beginTijd = ""
        self.guid = ""

    def to_dict(self):
        return {
            "homeTeam": self.homeTeam.to_dict(),
            "awayTeam": self.awayTeam.to_dict(),
            "teamThuisGUID": self.teamThuisGUID,
            "teamThuisNaam": self.teamThuisNaam,
            "teamUitGUID": self.teamUitGUID,
            "teamUitNaam": self.teamUitNaam,
            "datumString": self.datumString,
            "pouleGUID": self.pouleGUID,
            "pouleNaam": self.pouleNaam,
            "gespeeld": self.gespeeld,
            "uitslag": self.uitslag,
            "beginTijd": self.beginTijd,
            "guid": self.guid,
        }

def parse_events(events: List[Dict[str, Union[str, int]]]) -> GameStats:
    game_stats = GameStats()

    # Original logic for parsing events
    players_on_court = {"homeTeam": set(), "awayTeam": set()}

    for event in events:
        quarter = event["Periode"]
        team = "homeTeam" if event["TofU"] == "T" else "awayTeam"
        opponent_team = "awayTeam" if team == "homeTeam" else "homeTeam"
        player = event["RugNr"]

        if player not in game_stats.__getattribute__(team).players:
            game_stats.__getattribute__(team).players[player] = PlayerStats()

        player_stats = game_stats.__getattribute__(team).players[player]
        if quarter not in player_stats.quarters:
            player_stats.quarters[quarter] = {
                "totalPoints": 0,
                "onePointers": 0,
                "twoPointers": 0,
                "threePointers": 0,
                "fouls": 0,
                "minutesPlayed": 0,
                "inTime": None,
                "plusMinus": 0,
            }

        # Initialize quarter stats if not already present
        player_stats = game_stats.__getattribute__(team).players[player]
        if quarter not in player_stats.quarters:
            player_stats.quarters[quarter] = {
                "totalPoints": 0,
                "onePointers": 0,
                "twoPointers": 0,
                "threePointers": 0,
                "fouls": 0,
                "minutesPlayed": 0,
                "inTime": None,
                "plusMinus": 0
            }

        # Handle scoring events
        if event["GebType"] == 10 and event["GebStatus"] == 10:
            points_match = re.match(r"^(\d+) \(\d+-\d+\)$", event["Text"])
            if points_match:
                points = int(points_match.group(1))

                # Update team score
                game_stats.__getattribute__(team).totalPoints += points

                # Update plus-minus for players currently on the floor
                for on_court_player in players_on_court[team]:
                    game_stats.__getattribute__(team).players[on_court_player].plusMinus += points
                    game_stats.__getattribute__(team).players[on_court_player].quarters[quarter]["plusMinus"] += points

                for on_court_player in players_on_court[opponent_team]:
                    game_stats.__getattribute__(opponent_team).players[on_court_player].plusMinus -= points
                    game_stats.__getattribute__(opponent_team).players[on_court_player].quarters[quarter]["plusMinus"] -= points

                # Update individual player scoring stats
                player_stats.totalPoints += points
                player_stats.quarters[quarter]["totalPoints"] += points

                # Update point type
                if points == 1:
                    player_stats.onePointers += 1
                    player_stats.quarters[quarter]["onePointers"] += 1
                elif points == 2:
                    player_stats.twoPointers += 1
                    player_stats.quarters[quarter]["twoPointers"] += 1
                elif points == 3:
                    player_stats.threePointers += 1
                    player_stats.quarters[quarter]["threePointers"] += 1

        # Handle foul events
        elif event["GebType"] == 30 and event["GebStatus"] == 10:
            player_stats.fouls += 1
            player_stats.quarters[quarter]["fouls"] += 1

        # Handle substitution events
        elif event["GebType"] == 50 and event["GebStatus"] == 10:
            if event["Text"] == "in":
                player_stats.quarters[quarter]["inTime"] = event["Minuut"]
                players_on_court[team].add(player)
            elif event["Text"] == "uit":
                in_time = player_stats.quarters[quarter]["inTime"]
                if in_time is not None:
                    out_time = event["Minuut"]
                    minutes_played = out_time - in_time

                    player_stats.quarters[quarter]["minutesPlayed"] += minutes_played
                    player_stats.totalMinutesPlayed += minutes_played
                    player_stats.quarters[quarter]["inTime"] = None
                    players_on_court[team].discard(player)

        # Set RelGUID for the player
        player_stats.RelGUID = event["RelGUID"]

    # Handle end-of-quarter for players still on court
    for team_name in ["homeTeam", "awayTeam"]:
        for player in game_stats.__getattribute__(team_name).players.values():
            for quarter, stats in player.quarters.items():
                in_time = stats["inTime"]
                if in_time is not None:
                    minutes_played = 10 - in_time
                    stats["minutesPlayed"] += minutes_played
                    player.totalMinutesPlayed += minutes_played
                    stats["inTime"] = None

    # Normalize minutes played across quarters
    for team_name in ["homeTeam", "awayTeam"]:
        for quarter in range(1, 5):
            total_minutes_for_quarter = sum(
                player.quarters.get(quarter, {}).get("minutesPlayed", 0)
                for player in game_stats.__getattribute__(team_name).players.values()
            )

            if total_minutes_for_quarter != 50:
                normalization_factor = 50 / total_minutes_for_quarter if total_minutes_for_quarter > 0 else 1
                for player in game_stats.__getattribute__(team_name).players.values():
                    if quarter in player.quarters:
                        original_minutes = player.quarters[quarter]["minutesPlayed"]
                        adjusted_minutes = round(original_minutes * normalization_factor)
                        player.totalMinutesPlayed += adjusted_minutes - original_minutes
                        player.quarters[quarter]["minutesPlayed"] = adjusted_minutes

    return game_stats
