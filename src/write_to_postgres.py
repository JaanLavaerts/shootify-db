from datetime import datetime
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

def update_player_averages(cursor, player_guid):
    """
    Recalculate and update averages for a specific player based on all their games.
    """
    cursor.execute("""
        SELECT 
            AVG(total_points) as avg_points,
            AVG(one_pointers) as avg_one_pointers,
            AVG(two_pointers) as avg_two_pointers,
            AVG(three_pointers) as avg_three_pointers,
            AVG(fouls) as avg_fouls,
            AVG(total_minutes) as avg_minutes,
            AVG(plus_minus) as avg_plus_minus
        FROM PlayerGames
        WHERE player_guid = %s
    """, (player_guid,))
    
    averages = cursor.fetchone()
    
    cursor.execute("""
        UPDATE Players
        SET 
            avg_points = %s,
            avg_one_pointers = %s,
            avg_two_pointers = %s,
            avg_three_pointers = %s,
            avg_fouls = %s,
            avg_minutes = %s,
            avg_plus_minus = %s
        WHERE player_guid = %s
    """, (
        averages[0] or 0,  # avg_points
        averages[1] or 0,  # avg_one_pointers
        averages[2] or 0,  # avg_two_pointers
        averages[3] or 0,  # avg_three_pointers
        averages[4] or 0,  # avg_fouls
        averages[5] or 0,  # avg_minutes
        averages[6] or 0,  # avg_plus_minus
        player_guid
    ))

def initialize_database(db_config: dict):
    """
    Initialize the PostgreSQL database by creating necessary tables if they do not exist.
    """
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()

    # Create tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Games (
            game_guid TEXT PRIMARY KEY,
            home_team_guid TEXT NOT NULL,
            home_team_name TEXT NOT NULL,
            away_team_guid TEXT NOT NULL,
            away_team_name TEXT NOT NULL,
            date DATE,
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
            birthdate DATE,
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


def write_to_postgres(game_players, game_events, game_details, db_config):
    """
    Write data to the PostgreSQL database.
    """
    initialize_database(db_config)
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()

    # Extracting game details
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
        try:
            date_object = datetime.strptime(game_events.datumString, "%d-%m-%Y").date()
        except ValueError:
            date_object = None

        # Insert game data
        cursor.execute("""
            INSERT INTO Games (
                game_guid, home_team_guid, home_team_name, away_team_guid, away_team_name, date, poule_guid, poule_name, played, score, start_time
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (game_guid) DO NOTHING;
        """, (
            game_events.guid,
            game_events.teamThuisGUID,
            game_events.teamThuisNaam,
            game_events.teamUitGUID,
            game_events.teamUitNaam,
            date_object,
            game_events.pouleGUID,
            game_events.pouleNaam,
            game_events.gespeeld,
            game_events.uitslag.replace(" ", ""),
            game_events.beginTijd.replace(".", ":"),
        ))

        # Process player details
        detail_lookup = {detail["RelGUID"]: detail for detail in game_players["TtDeel"] + game_players["TuDeel"]}
        cursor.execute("SELECT player_guid, total_games FROM Players")
        existing_players = {row[0]: row[1] for row in cursor.fetchall()}

        players_to_update = set()

        for team_name, team_stats in {"homeTeam": game_events.homeTeam, "awayTeam": game_events.awayTeam}.items():
            team_guid = game_events.teamThuisGUID if team_name == "homeTeam" else game_events.teamUitGUID
            for player_id, player_stats in team_stats.players.items():
                player_guid = player_stats.RelGUID
                player_name = detail_lookup.get(player_guid, {}).get("Naam", "Unknown")

                birthdate_string = detail_lookup.get(player_guid, {}).get("GebDat", None)
                try:
                    player_birthdate = datetime.strptime(birthdate_string.split(" ")[0], "%d-%m-%Y").date() if birthdate_string else None
                except ValueError:
                    player_birthdate = None

                # Add player to update set
                players_to_update.add(player_guid)
                
                if player_guid in existing_players:
                    total_games = existing_players[player_guid] + 1
                    cursor.execute("""
                        UPDATE Players
                        SET total_games = %s
                        WHERE player_guid = %s;
                    """, (total_games, player_guid))
                else:
                    cursor.execute("""
                        INSERT INTO Players (
                            player_guid, name, birthdate, total_games
                        ) VALUES (%s, %s, %s, %s)
                        ON CONFLICT (player_guid) DO NOTHING;
                    """, (player_guid, player_name, player_birthdate, 1))

                cursor.execute("""
                    INSERT INTO PlayerGames (
                        player_guid, game_guid, team_guid, total_points, one_pointers,
                        two_pointers, three_pointers, fouls, total_minutes, plus_minus
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (player_guid, game_guid) DO NOTHING;
                """, (
                    player_guid, game_events.guid, team_guid,
                    player_stats.totalPoints, player_stats.onePointers, player_stats.twoPointers,
                    player_stats.threePointers, player_stats.fouls, player_stats.totalMinutesPlayed,
                    player_stats.plusMinus
                ))

        for player_guid in players_to_update:
            update_player_averages(cursor, player_guid)

        print(f"Inserted game {game_events.guid} into database.")

        conn.commit()

    except psycopg2.Error as e:
        print(f"Database error: {e}")
        raise

    finally:
        conn.close()
