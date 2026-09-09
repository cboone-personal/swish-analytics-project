# Swish Analytics data engineering take-home

Works out which 10 players were on the floor for every play in the provided
play-by-play data and writes the result to a MySQL table called
`pbp_players_on_court`.

Part 1 is the script `on_court.py`, the mysqldump in
`sql/pbp_players_on_court.sql`, and the writeup in
[docs/walkthrough.md](docs/walkthrough.md).

Part 2 is [docs/system-design.md](docs/system-design.md) with the diagram at
`docs/system-design.drawio.png`.

## Prerequisites

Python 3.11 or newer, and Docker Desktop.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
docker compose up -d
```

On Mac or Linux the second and fourth lines are `source .venv/bin/activate` and
`cp .env.example .env`.

Set the two passwords in `.env` to anything. The container and the script both
read that file. Check MySQL is up with `docker compose ps`, which should say
`healthy`.

## Running it

```bash
python on_court.py --game all --validate
```

- `--game` (required): an event_id such as `1947160`, or `all`
- `--validate`: run the output checks before writing
- `--no-db`: build and validate only, no MySQL write. Does not need `.env` or Docker.
- `--load-source`: also load pbp, pbp_players and rosters so the queries in `sql/` can run

Re-running is safe. Each game's rows are replaced in one transaction.

## Files

```
on_court.py    the script
data/          the three provided xlsx files
sql/           mysqldump of the output table, plus the two validation queries
docs/          both writeups and the diagram
```
