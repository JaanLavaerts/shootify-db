### .ENV

```env
DB_NAME=
DB_USER=
DB_PASSWORD=
DB_HOST=
DB_PORT=
```

## Steps when on VPS

Everything from root directory

1. run python3 util/get_guids_of_played_games.py > ./src/played_games.txt
2. run step_one.py to insert the already played games into the database
3. setup cron job to run step_2.py every 5 minutes to check todays played games and insert them into the database
4. setup cronjob to clear the played_games.txt file every 24 hours
