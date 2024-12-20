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
