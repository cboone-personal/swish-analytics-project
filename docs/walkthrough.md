
# on_court.py walkthrough

The main function of `on_court.py` is to figure out which 10 players were on the floor for every play in the `pbp` data set and write that data into a MySQL table named `pbp_players_on_court`.


## Setup (one time)

Needs Python 3.11+ and Docker Desktop.

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
docker compose up -d
```
Check MySQL is up with `docker compose ps`. Status should say `healthy`.


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

5. `walk_plays` produces the output table. It loops through each team's plays in order, beginning with each period's starting five, swapping players at each substitution, and records who is on the floor at every play (10 rows per play).

6. `validate` checks the output before it is written. 
     - Every `play_id` in `pbp` appears in the output. 
     - Every play has exactly 10 rows. 
     - Every play has exactly 5 rows for each team. 
     - Every player appears on that game's roster. 
     - No play lists the same player twice. 
     - Any failure stops the script with a message saying which check failed.

7. `write_table` writes the output DataFrame to MySQL. It creates the table if it does not exist, then for each game in the DataFrame it deletes that game's existing rows and inserts the new ones with an updated `updated_at` timestamp.

## Why the code is built this way

Everything is in one file. The script is about 400 lines and a quarter of that is SQL for the table definitions, so there is not much to gain from splitting it into modules.

I built this in a Jupyter notebook one function at a time, running each one and looking at what came back before writing the next. Keeping them independent meant I could rerun a single step without rerunning everything before it. `on_court.py` is that notebook exported with a `main` function added at the end.

`walk_plays` has the only loop. Everything else is pandas operations on whole frames, which is shorter and faster than iterating over rows.

`attach_roster_team` runs once at the start so the rest of the script can trust `team_id`. The alternative was looking the roster up in three or four different places, which is more code and more places to get it wrong.

`validate` is separate from the write so the checks can run with `--no-db` and no MySQL at all.

## Inferring period starters

There are no substitution events between periods. If a different set of players starts a period than the ones who finished the period before, the data just continues with new players appearing, so the Q2, Q3, and Q4 lineups have to be inferred.

Take each player's first row in the period. If it is a substitution with that player checking in, that means he started on the bench. Any other play type (shot, rebound, foul, etc.) means the player was already on the floor. Technical fouls are ignored because they can be called on bench players.

```python
evidence = pbpp[(pbpp.period >= 2) & (pbpp.play_detail != TECHNICAL)]
first_row = evidence.drop_duplicates(subset=OPENER_COLS, keep="first")
checked_in = (first_row.play_event == "Substitution") & (first_row.sequence == SUB_IN)
inferred = first_row.loc[~checked_in, OPENER_COLS]
```

Two rows in the data break this rule:

- `play_id 149` (*game 1947312*) incorrectly tags Devin Booker as Houston even though he plays for Phoenix. Using the feed's team column puts a sixth player on Houston's Q2 lineup. This is why step 2 takes team from `rosters`.
- `play_id 393` (*game 1947312*) is a technical foul on T.J. Warren from the bench. Counting it puts a sixth player on Phoenix's Q4 lineup. This is why technicals are excluded.

With both issues handled, all 16 game/period/team groups come out to exactly 5. Running the same rule on Q1, where the answer is given, reproduces the 20 listed starters.

Substitutions take effect on their own play row, so the incoming player counts as on the floor for that play. Sub rows never score, so this makes no difference to any points calculation.

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

The table has one row per player per play, so 10 rows for every play.

Team points while a player was on court is a join to `pbp` on `event_id` and `play_id`, grouped by `player_id`. `team_id`, `period` and `is_home` are on the table so that query does not also have to join `rosters` and `pbp` to get them.

`ix_player` covers per-player lookups. `ix_team` covers a team's lineup across the game.

Reruns delete the game's rows and reinsert them in one transaction. An upsert would leave old rows behind if a play were removed from the source. If anything fails before the commit the table is unchanged.

## Results

`sql/validation1.sql` sums team points for and against while each player was on court, which is the calculation the prompt describes. Top of the output across both games:

| event_id | team_id | name | pts_for | pts_against | plays |
|---|---|---|---:|---:|---:|
| 1947312 | 10 | Trevor Ariza | 111 | 89 | 362 |
| 1947312 | 10 | James Harden | 108 | 93 | 354 |
| 1947312 | 10 | Ryan Anderson | 95 | 73 | 292 |
| 1947312 | 10 | P.J. Tucker | 92 | 80 | 361 |
| 1947312 | 21 | Devin Booker | 84 | 107 | 306 |


`sql/validation2.sql` checks that the sum of points for all players on a team is exactly five times the team's total, since each point is credited to all five players on the floor.

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

`sql/pbp_players_on_court.sql` is a mysqldump of the table. Loaded into an empty database, it has 9,930 rows.

## Time complexity

Everything except the loop reads each row once, apart from the three sorts in `load`.

The loop is the one part that would not scale. `walk_plays` filters the full `subs` and `plays` frames once per group, and both the group count and the play count grow with the number of games, so the work goes up with games squared. Two games is 16 groups against 993 plays and it finishes instantly. A season would not. Running one game at a time avoids it.

Output is ten rows per play, 9,930 for two games.

## Shortcomings

- A starter with no event in a period (no shot, rebound, foul, etc.) would be missed and that team would come out to four. This does not happen in these two games. A fallback would be the previous period's closing lineup.
- Substitution direction is read from `sequence`. I checked it against `play_text` for these games but the code does not parse the text.
- Overtime uses the same rule as Q2 to Q4 but there is no overtime in this data to test it on.
- The 5x reconciliation confirms the join and the play counts. Any five players would satisfy it, so it cannot confirm the right five are on the floor.
- `sub_events` keeps one incoming and one outgoing player per play. If a feed ever recorded two substitutions for the same team on the same `play_id`, the second pair would be dropped and `validate` would not catch it, since the count would still be five.
