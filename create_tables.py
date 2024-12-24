import os
from dotenv import load_dotenv
import psycopg2

# Load environment variables from .env
load_dotenv()

# Get database credentials
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

# SQL script to create tables
CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS Games (
    game_guid TEXT PRIMARY KEY,
    home_team_guid TEXT NOT NULL,
    home_team_name TEXT NOT NULL,
    away_team_guid TEXT NOT NULL,
    away_team_name TEXT NOT NULL,
    date DATE NOT NULL,
    poule_guid TEXT NOT NULL,
    poule_name TEXT NOT NULL,
    played TEXT NOT NULL,
    score TEXT NOT NULL,
    start_time TEXT NOT NULL
);

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
"""

def create_tables():
    try:
        # Connect to PostgreSQL database
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cursor = conn.cursor()

        # Execute the SQL script
        cursor.execute(CREATE_TABLES_SQL)
        conn.commit()
        print("Tables created successfully!")

    except psycopg2.Error as e:
        print(f"Error while creating tables: {e}")
    finally:
        if conn:
            cursor.close()
            conn.close()

if __name__ == "__main__":
    create_tables()
