# NBA "who's on the court" — Swish Analytics DE take-home

Works out which 10 players were on the floor for every play in the provided
play-by-play data and writes the result to a MySQL table called
`pbp_players_on_court`.

**Part 1** — the script is `on_court.py`. The writeup is [docs/walkthrough.md](docs/walkthrough.md),
and the mysqldump of the output table is `sql/pbp_players_on_court.sql`.

**Part 2** — [docs/system-design.md](docs/system-design.md) and the diagram at
`docs/system-design.drawio.png`.

Setup and run instructions are at the top of the Part 1 writeup.

```
on_court.py    the script
data/          the three provided xlsx files
sql/           mysqldump of the output table, plus the two validation queries
docs/          both writeups and the diagram
```
