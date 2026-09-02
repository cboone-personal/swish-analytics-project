# NBA "Who's On the Court" — Swish Analytics DE Take-Home

Derives the 10 players on the floor for every play in the provided NBA
play-by-play data and loads the result to a MySQL table `pbp_players_on_court`.

- **Part 1** — `on_court.py` + `sql/pbp_players_on_court.sql` + `docs/walkthrough.md`
- **Part 2** — `docs/system-design.drawio.png` + `docs/system-design.md`

## Quick start

Prereqs: Python 3.11+, Docker Desktop.

```bash
# 1. python env
python -m venv .venv
.venv\Scripts\activate          # windows   |   source .venv/bin/activate  (mac/linux)
pip install -r requirements.txt

# 2. mysql (docker)
copy .env.example .env          # then edit passwords
docker compose up -d

# 3. run
python on_court.py --game all             # every game in the data
python on_court.py --game 1947160         # one game
python on_court.py --game all --validate  # run + integrity checks + points-on-court report

# 4. tests
pytest -q
```

Re-running is safe: each game's rows are replaced atomically.

## Inputs

| file | rows | what |
|---|---|---|
| `data/pbp.xlsx` | 1,011 | play-by-play, one row per play (play_id 1 = starting lineup, 10 rows) |
| `data/pbp-players.xlsx` | 1,357 | same plays, one row per involved player |
| `data/rosters.xlsx` | 66 | game rosters — authoritative player→team |

## Output

`pbp_players_on_court` — one row per `(event_id, play_id, player_id)`.
10 rows per play. Columns: `event_id, play_id, player_id, team_id, period, is_home, updated_at`.

Example — team points scored while each player was on court:

```sql
-- see sql/validation.sql
```

## Repo map

```
on_court.py               the script (sectioned; runs top-to-bottom or cell-by-cell)
test_on_court.py          pytest
data/                     provided xlsx
sql/                      mysqldump + validation queries
docs/                     writeups, diagram, original prompt
scratch/                  exploration, not a deliverable
docker-compose.yml        mysql:8.4
.env.example              connection template (no secrets committed)
```
