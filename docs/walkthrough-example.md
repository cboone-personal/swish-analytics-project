# on_court.py walkthrough

(example for shape only. rewrite in your words. delete before zipping.)

`on_court.py` figures out which 10 players were on the floor for every play in the `pbp` data set and writes that to a MySQL table named `pbp_players_on_court`. It runs for one game or all games and can be rerun without duplicating rows.

## Setup (once)

Needs Python 3.11+ and Docker Desktop. See `README.md` for the full commands.

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
docker compose up -d
```

Set `MYSQL_PASSWORD` and `MYSQL_ROOT_PASSWORD` in `.env`. Any values work; the container and the script both read this file. Check MySQL is up with `docker compose ps`. Status should say `healthy`.

## Running the script

```bash
python on_court.py --game all --validate
```

Arguments:

- `--game` (required): an event_id such as `1947160`, or `all`
- `--validate`: run the output checks before writing
- `--no-db`: build and validate only, no MySQL write. Does not need `.env` or Docker.
- `--load-source`: also load `pbp`, `pbp_players` and `rosters` into MySQL so the queries in `sql/` can run

## Input data

`pbp` has one row per play: what happened, which team, when, and points scored. No players. `play_id` counts up through the game, so sorting by it gives play order.

`pbp_players` has one row per player involved in a play. A substitution is two rows with the same `play_id`: `sequence = 1` is the player coming in, `sequence = 2` is the player going out. `play_id 1` is the starting lineup, ten rows.

`rosters` has each player on each game's roster with his `team_id`.

## How it works

1. `load` reads the three xlsx files into pandas DataFrames, casts the id columns to int (they load as floats because other columns have blanks), drops `pbp_players` rows with no `player_id` (timeouts, period start/end, team rebounds), and sorts by `event_id, play_id, play_sequence`.

2. `attach_roster_team` overwrites `team_id` in `pbp_players` with the player's `team_id` from `rosters`. The feed's own team column is wrong on one row (see Inferring period starters).

3. `period_openers` finds the five players on the floor per team at the start of each period. Q1 comes from the ten starting lineup rows. Q2 onward is inferred from each player's first appearance in the period (next section). 80 rows.

4. `sub_events` collapses each substitution's two rows into one row with `player_in` and `player_out`. 104 rows.

5. `walk_plays` produces the output table. For each team and period it starts with the five from step 3, goes through the plays in order, swaps players at each substitution, and records who is on the floor at every play. 10 rows per play, 9,930 rows.

6. `validate` checks the output before it is written:
   - every `play_id` in `pbp` appears in the output
   - every play has exactly 10 rows
   - every play has exactly 5 rows per team
   - every player is on that game's roster
   - no play lists the same player twice

   Any failure stops the script with a message saying which check failed.

7. `write_table` writes a DataFrame to MySQL. It creates the table if it does not exist, then for each game deletes that game's rows and inserts the new ones, in one transaction. The same function loads the three input tables under `--load-source`.

Steps 1 to 4 and 6 are pandas operations on whole frames. Step 5 is the only loop.

## Inferring period starters

There are no substitution events between periods. Coaches change the five during the break and the data just resumes with new players appearing, so the Q2, Q3 and Q4 lineups have to be inferred.

For each player, take his first row in the period. If it is a substitution with him coming in, he started on the bench. Anything else (a shot, rebound, foul, or being subbed out) means he was already on the floor. Technical fouls are ignored because they can be called on bench players.

```python
evidence = pbpp[(pbpp.period >= 2) & (pbpp.play_detail != TECHNICAL)]
first_row = evidence.drop_duplicates(subset=OPENER_COLS, keep="first")
checked_in = (first_row.play_event == "Substitution") & (first_row.sequence == SUB_IN)
inferred = first_row.loc[~checked_in, OPENER_COLS]
```

Two rows in the data break this rule:

- `play_id 149` (game 1947312) tags Devin Booker as Houston. He plays for Phoenix. Using the feed's team column puts a sixth player on Houston's Q2 lineup. This is why step 2 takes team from `rosters`.
- `play_id 393` (game 1947312) is a technical foul on T.J. Warren from the bench. Counting it puts a sixth player on Phoenix's Q4 lineup. This is why technicals are excluded.

With both handled, all 16 game/period/team groups come out to exactly 5. Running the same rule on Q1, where the answer is given, reproduces the 20 listed starters.

Substitutions take effect on their own play row. Sub rows never score, so this does not affect any points calculation.

## Table design

```sql
CREATE TABLE pbp_players_on_court (
  event_id   INT        NOT NULL,
  play_id    INT        NOT NULL,
  player_id  INT        NOT NULL,
  team_id    INT        NOT NULL,
  period     INT        NOT NULL,
  is_home    INT        NOT NULL,
  updated_at TIMESTAMP  NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (event_id, play_id, player_id),
  KEY ix_player (event_id, player_id),
  KEY ix_team   (event_id, team_id, play_id)
);
```

One row per play per player, 10 per play. Team points while a player was on court is one join to `pbp` on `event_id, play_id` and a group by `player_id`. `team_id`, `period` and `is_home` are kept on the table so the common queries do not have to join back to `pbp` and `rosters`. `ix_player` covers per-player lookups, `ix_team` covers a team's lineup over the game.

Reruns delete the game's rows and reinsert them in one transaction. An upsert would leave old rows behind if a play were removed from the source. If anything fails before the commit the table is unchanged.

## Results

`sql/validation1.sql` sums team points for and against while each player was on court. `sql/validation2.sql` checks that the sum over a team's players is exactly 5x the team's total, since every point is on the floor for five players.

| event_id | team_id | team_pts | on_court_pts | on_court_pts - 5 x team_pts |
|---|---|---:|---:|---:|
| 1947160 | 2 | 92 | 460 | 0 |
| 1947160 | 9 | 88 | 440 | 0 |
| 1947312 | 10 | 142 | 710 | 0 |
| 1947312 | 21 | 116 | 580 | 0 |

Team totals match the final scores in `pbp`.

```text
python on_court.py --game all --validate --no-db   validate passed: 9930 rows, 993 plays, 2 games
python on_court.py --game 1947160                  wrote 4890 rows for 1 game(s)
python on_court.py --game all --validate           wrote 9930 rows for 2 game(s)
python on_court.py --game all                      wrote 9930 rows for 2 game(s)   (table count still 9930)
python on_court.py --game 999                      error: event_id 999 not found in pbp
```

`sql/pbp_players_on_court.sql` is a mysqldump of the table. Loaded into an empty database it has 9,930 rows.

## Time complexity

N = rows in `pbp_players` (1,284), P = plays (993). The sort in `load` is O(N log N). The roster join, `drop_duplicates` for openers and the substitution pivot are O(N). The walk visits each play once per team and emits 5 rows each time, O(P). The write is one batched insert per game. Overall O(N log N), memory O(N + 10P).

Games share no state, so runtime scales linearly with games and parallelizes across them. A full season is about 600,000 plays and 6,000,000 output rows.

## Shortcomings

- A starter with no event in a period (no shot, rebound, foul or sub) would be missed and that team would come out to four. Does not happen in these two games. A fallback would be the previous period's closing lineup.
- Substitution direction is read from `sequence`. I checked it against `play_text` for these games but the code does not parse the text.
- Overtime uses the same rule as Q2 to Q4 but there is no overtime in this data to test it on.
- `rosters` is trusted for player to team. Nothing checks it.
- An ejection or injury with no substitution event would leave a team at four. `validate` fails rather than guessing.
- Column types for the three input tables were sized to these two games.

Next additions would be a stint table (one row per continuous spell on the floor) for plus/minus and minutes, and a pytest file with a hand-built three-play case for the substitution logic.
