import sqlite3

def initialize_database(db_path: str):
    """
    Initialize the SQLite database by creating necessary tables if they do not exist.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Games (
            game_guid TEXT PRIMARY KEY,
            home_team_guid TEXT NOT NULL,
            home_team_name TEXT NOT NULL,
            away_team_guid TEXT NOT NULL,
            away_team_name TEXT NOT NULL,
            date TEXT NOT NULL,
            poule_guid TEXT NOT NULL,
            poule_name TEXT NOT NULL,
            played TEXT NOT NULL,
            score TEXT NOT NULL,
            start_time TEXT NOT NULL
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Players (
            player_guid TEXT PRIMARY KEY,
            name TEXT,
            total_games INTEGER DEFAULT 0,
            avg_points REAL DEFAULT 0,
            avg_one_pointers REAL DEFAULT 0,
            avg_two_pointers REAL DEFAULT 0,
            avg_three_pointers REAL DEFAULT 0,
            avg_fouls REAL DEFAULT 0,
            avg_minutes REAL DEFAULT 0,
            avg_plus_minus REAL DEFAULT 0
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS PlayerGames (
            player_guid TEXT NOT NULL,
            game_guid TEXT NOT NULL,
            team_guid TEXT NOT NULL,
            total_points INTEGER DEFAULT 0,
            one_pointers INTEGER DEFAULT 0,
            two_pointers INTEGER DEFAULT 0,
            three_pointers INTEGER DEFAULT 0,
            fouls INTEGER DEFAULT 0,
            total_minutes INTEGER DEFAULT 0,
            plus_minus INTEGER DEFAULT 0,
            PRIMARY KEY (player_guid, game_guid),
            FOREIGN KEY (player_guid) REFERENCES Players(player_guid),
            FOREIGN KEY (game_guid) REFERENCES Games(game_guid)
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Quarters (
            game_guid TEXT NOT NULL,
            team_guid TEXT NOT NULL,
            quarter INTEGER NOT NULL,
            total_points INTEGER DEFAULT 0,
            one_pointers INTEGER DEFAULT 0,
            two_pointers INTEGER DEFAULT 0,
            three_pointers INTEGER DEFAULT 0,
            fouls INTEGER DEFAULT 0,
            PRIMARY KEY (game_guid, team_guid, quarter),
            FOREIGN KEY (game_guid) REFERENCES Games(game_guid)
        );
    """)
    conn.commit()
    conn.close()


def write_to_sqlite(game_players, game_events, game_details, db_path):
    
    initialize_database(db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    game_events.teamThuisGUID = game_details.get("teamThuisGUID", "")
    game_events.teamThuisNaam = game_details.get("teamThuisNaam", "")
    game_events.teamUitGUID = game_details.get("teamUitGUID", "")
    game_events.teamUitNaam = game_details.get("teamUitNaam", "")
    game_events.datumString = game_details.get("datumString", "")
    game_events.pouleGUID = game_details.get("pouleGUID", "")
    game_events.pouleNaam = game_details.get("pouleNaam", "")
    game_events.gespeeld = game_details.get("gespeeld", "")
    game_events.uitslag = game_details.get("uitslag", "")
    game_events.beginTijd = game_details.get("beginTijd", "")
    game_events.guid = game_details.get("guid", "")

    try:
        # Existing game data insertion
        game_guid = game_events.guid
        cursor.execute("""
            INSERT INTO Games (
                game_guid, home_team_guid, home_team_name, away_team_guid, away_team_name, date, poule_guid, poule_name, played, score, start_time
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            game_guid,
            game_events.teamThuisGUID,
            game_events.teamThuisNaam,
            game_events.teamUitGUID,
            game_events.teamUitNaam,
            game_events.datumString,
            game_events.pouleGUID,
            game_events.pouleNaam,
            game_events.gespeeld,
            game_events.uitslag.replace(" ", ""),
            game_events.beginTijd.replace(".", ":"),
        ))

        # Process both teams' quarter statistics
        teams_data = [
            (game_events.teamThuisGUID, game_events.homeTeam),
            (game_events.teamUitGUID, game_events.awayTeam)
        ]

        for team_guid, team_stats in teams_data:
            # Initialize quarter stats for quarters 1-4
            quarter_stats = {
                1: {'total_points': 0, 'one_pointers': 0, 'two_pointers': 0, 'three_pointers': 0, 'fouls': 0},
                2: {'total_points': 0, 'one_pointers': 0, 'two_pointers': 0, 'three_pointers': 0, 'fouls': 0},
                3: {'total_points': 0, 'one_pointers': 0, 'two_pointers': 0, 'three_pointers': 0, 'fouls': 0},
                4: {'total_points': 0, 'one_pointers': 0, 'two_pointers': 0, 'three_pointers': 0, 'fouls': 0}
            }

            # Aggregate stats from all players for each quarter
            for player in team_stats.players.values():
                for quarter, stats in player.quarters.items():
                    # Only process quarters 1-4
                    if quarter not in range(1, 5):
                        continue
                        
                    quarter_stats[quarter]['total_points'] += stats.get('totalPoints', 0)
                    quarter_stats[quarter]['one_pointers'] += stats.get('onePointers', 0)
                    quarter_stats[quarter]['two_pointers'] += stats.get('twoPointers', 0)
                    quarter_stats[quarter]['three_pointers'] += stats.get('threePointers', 0)
                    quarter_stats[quarter]['fouls'] += stats.get('fouls', 0)

            # Insert quarter statistics for each quarter
            for quarter in range(1, 5):  # Explicitly handle quarters 1-4
                stats = quarter_stats[quarter]
                cursor.execute("""
                    INSERT INTO Quarters (
                        game_guid, team_guid, quarter, total_points, one_pointers,
                        two_pointers, three_pointers, fouls
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    game_guid,
                    team_guid,
                    quarter,
                    stats['total_points'],
                    stats['one_pointers'],
                    stats['two_pointers'],
                    stats['three_pointers'],
                    stats['fouls']
                ))

        # Process player details and update player averages
        detail_lookup = {detail["RelGUID"]: detail for detail in game_players["TtDeel"] + game_players["TuDeel"]}
        cursor.execute("SELECT player_guid, total_games, avg_points, avg_one_pointers, avg_two_pointers, avg_three_pointers, avg_fouls, avg_minutes, avg_plus_minus FROM Players")
        existing_players = {row[0]: row[1:] for row in cursor.fetchall()}

        # Handle player statistics (rest of the existing code)
        teams = {"homeTeam": game_events.homeTeam, "awayTeam": game_events.awayTeam}
        team_guids = {"homeTeam": game_events.teamThuisGUID, "awayTeam": game_events.teamUitGUID}

        for team_name, team_stats in teams.items():
            team_guid = team_guids[team_name]

            for player_id, player_stats in team_stats.players.items():
                player_guid = player_stats.RelGUID
                player_name = detail_lookup.get(player_guid, {}).get("Naam", "Unknown")

                if player_guid in existing_players:
                    # Update averages
                    total_games, avg_points, avg_one_pointers, avg_two_pointers, avg_three_pointers, avg_fouls, avg_minutes, avg_plus_minus = existing_players[player_guid]
                    total_games += 1

                    updated_values = {
                        "avg_points": round((avg_points * (total_games - 1) + player_stats.totalPoints) / total_games, 1),
                        "avg_one_pointers": round((avg_one_pointers * (total_games - 1) + player_stats.onePointers) / total_games, 1),
                        "avg_two_pointers": round((avg_two_pointers * (total_games - 1) + player_stats.twoPointers) / total_games, 1),
                        "avg_three_pointers": round((avg_three_pointers * (total_games - 1) + player_stats.threePointers) / total_games, 1),
                        "avg_fouls": round((avg_fouls * (total_games - 1) + player_stats.fouls) / total_games, 1),
                        "avg_minutes": round((avg_minutes * (total_games - 1) + player_stats.totalMinutesPlayed) / total_games, 1),
                        "avg_plus_minus": round((avg_plus_minus * (total_games - 1) + player_stats.plusMinus) / total_games, 1),
                    }

                    cursor.execute("""
                        UPDATE Players SET
                            total_games = ?, avg_points = ?, avg_one_pointers = ?, avg_two_pointers = ?,
                            avg_three_pointers = ?, avg_fouls = ?, avg_minutes = ?, avg_plus_minus = ?
                        WHERE player_guid = ?
                    """, (
                        total_games,
                        updated_values["avg_points"],
                        updated_values["avg_one_pointers"],
                        updated_values["avg_two_pointers"],
                        updated_values["avg_three_pointers"],
                        updated_values["avg_fouls"],
                        updated_values["avg_minutes"],
                        updated_values["avg_plus_minus"],
                        player_guid,
                    ))
                else:
                    # Insert new player
                    cursor.execute("""
                        INSERT INTO Players (
                            player_guid, name, total_games, avg_points, avg_one_pointers, avg_two_pointers,
                            avg_three_pointers, avg_fouls, avg_minutes, avg_plus_minus
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        player_guid, player_name, 1,
                        player_stats.totalPoints, player_stats.onePointers, player_stats.twoPointers,
                        player_stats.threePointers, player_stats.fouls, player_stats.totalMinutesPlayed,
                        player_stats.plusMinus,
                    ))

                # Insert player game stats
                cursor.execute("""
                    INSERT INTO PlayerGames (
                        player_guid, game_guid, team_guid, total_points, one_pointers, two_pointers, three_pointers,
                        fouls, total_minutes, plus_minus
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    player_guid, game_guid, team_guid,
                    player_stats.totalPoints, player_stats.onePointers, player_stats.twoPointers,
                    player_stats.threePointers, player_stats.fouls, player_stats.totalMinutesPlayed,
                    player_stats.plusMinus,
                ))

        conn.commit()

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        raise

    finally:
        conn.close()