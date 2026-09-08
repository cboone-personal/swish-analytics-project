# on_court.py walkthrough

The main function of `on_court.py` is to figure out which 10 players were on the floor for every play in the `pbp` data set and write that data into a MySQL table named `pbp_players_on_court`.


## Setup (once)
(*see `README.md` for exact commands.*)

Needs Python 3.11+ and Docker Desktop.

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
docker compose up -d
```
Check MySQL is up with `docker compose ps`. Status should say `healthy`


## Running the script

```bash
python on_court.py --game all --validate
```

### Arguments:

- `--game` (required): an event_id such as `1947160`, or `all`
- `--validate`: run the output checks before writing
- `--no-db`: build and validate only, no MySQL write
- `--load-source`: also load pbp, pbp_players and rosters so the queries in `sql/` folder can run

## How it works

1. `load` reads the three xlsx files into pandas DataFrames, cleans the column types, and sorts by the main ID fields. Id columns come in as floats because other columns have blanks, so they are cast to int.

2. `attach_roster_team` overwrites `team_id` in `pbp_players` with the player's `team_id` from `rosters` (the feed's own team column is wrong on one row, see the next section for details).

3. `period_openers` finds the five players on the floor per team at the start of each period. Q1 comes from the ten starting lineup rows. Q2 onward is inferred from each player's first appearance in the period (see next section).

4. `sub_events` collapses each substitution's two rows (`player_in`, `player_out`) into one row.

5. `walk_plays` produces the output table. It loops through each team's plays in o   rder, beginning with each period's starting five, swapping players at each substitution, and records who is on the floor at every play (10 rows per play).

6. `validate` checks the output before it is written. 
     - Every `play_id` in `pbp` appears in the output. 
     - Every play has exactly 10 rows. 
     - Every play has exactly 5 rows for each team. 
     - Every player appears on that game's roster. 
     - No play lists the same player twice. 
     - Any failure stops the script with a message saying which check failed.

7. `write_table` writes the output DataFrame to MySQL. It creates the table if it does not exist, then for each game in the DataFrame it deletes that game's existing rows and inserts the new ones with an updated `updated_at` timestamp.


