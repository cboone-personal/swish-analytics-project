# Step-by-step plan

Your roadmap. Check boxes as you go. Each phase ends with a **✅ Done when**
gate — don't move on until it's true. Phases 0–2 are setup; 3–5 are the code;
6–7 are the writeups; 8 is packaging.

Ground rule for Claude in this repo: you write the code, Claude guides.
Pseudocode below is the *shape*, not the answer. Type it your way.

---

## Phase 0 — Environment (≈30 min)

### 0.1 VS Code + repo

- [ ] Open VS Code → `File > Open Folder` → `C:\Users\ChrisBoone\swish-analytics-project`
- [ ] VS Code will prompt "install recommended extensions" (from `.vscode/extensions.json`). Say yes. If it doesn't: `Ctrl+Shift+X`, search `@recommended`, install all.
  - Python, Pylance — language
  - Jupyter — gives you `# %%` cells + Interactive Window
  - SQLTools + MySQL driver — browse the table without leaving VS Code
  - Draw.io Integration — edit the Part 2 diagram in VS Code
  - Docker — see the container status in the sidebar
  - Claude Code — Claude in the editor

### 0.2 Git identity — **do this before your first commit**

Your global git identity is your work one (`cboone-panthers` /
`@teppersportsentertainment.com`). This repo is under `cboone-personal`.
Set a **repo-local** identity so commits carry your personal name/email:

```bash
git config user.name "Chris Boone"
```
```bash
git config user.email "YOUR_PERSONAL_EMAIL"
```

(no `--global` → only affects this repo.)

### 0.3 Python venv

In the VS Code terminal (`` Ctrl+` ``), from the repo root:

```bash
python -m venv .venv
```
```bash
.venv\Scripts\activate
```
```bash
pip install -r requirements.txt
```

- [ ] Bottom-right of VS Code shows `.venv` as the interpreter. If not: `Ctrl+Shift+P` → "Python: Select Interpreter" → pick `.venv`.

### 0.4 Test the `# %%` loop

- [ ] Open `scratch/explore.py`. Under the `# %%` type `1 + 1`. Press `Shift+Enter`. Interactive Window opens on the right, shows `2`. That's your dev loop for the whole project.

### 0.5 Claude in VS Code

- [ ] VS Code terminal → `claude`. It reads `CLAUDE.md` automatically; it knows the algorithm, the gotchas, and that you write the code.
- [ ] Or use the Claude Code extension panel (sidebar icon). Same thing.

**✅ Done when:** `Shift+Enter` on a cell prints output, `pip list` shows pandas + mysql-connector-python, `git config user.email` shows your personal address.

---

## Phase 1 — MySQL in Docker (≈30 min, first time)

You've not done this before. Here's every click.

### 1.1 Start Docker Desktop

- [ ] Windows Start → "Docker Desktop" → launch. Wait until the whale icon in the system tray stops animating (30–60 s). The engine wasn't running when we checked.
- [ ] Verify in terminal:

```bash
docker info --format "{{.ServerVersion}}"
```

Prints a version → good. Prints "cannot connect" → Docker Desktop not up yet.

### 1.2 Make your `.env`

- [ ] Copy the template:

```bash
copy .env.example .env
```

- [ ] Open `.env`, change `MYSQL_PASSWORD` and `MYSQL_ROOT_PASSWORD` to anything. Doesn't need to be strong — it's a local throwaway DB. `.env` is gitignored; it never leaves your machine.

### 1.3 Start MySQL

```bash
docker compose up -d
```

First run downloads the `mysql:8.4` image (~600 MB, a minute or two). Then:

```bash
docker compose ps
```

- [ ] `STATUS` column says `healthy` (may say `starting` for ~15 s first). If it says `unhealthy` or `exited`:

```bash
docker compose logs mysql --tail 50
```

Common cause: port 3306 already in use (a leftover local MySQL). Fix: change `MYSQL_PORT=3307` in `.env`, `docker compose down`, `docker compose up -d`.

### 1.4 Connect and look around

Get a MySQL shell *inside* the container (no MySQL client needed on Windows):

```bash
docker exec -it swish-mysql mysql -u swish -p swish
```

Type your `MYSQL_PASSWORD`. You're in. Try:

```sql
SHOW DATABASES;
SHOW TABLES;      -- empty for now
SELECT VERSION();
exit
```

- [ ] You saw the `swish` database.

### 1.5 SQLTools (optional but nice)

- [ ] SQLTools sidebar icon → connection "swish-mysql (docker)" is pre-configured in `.vscode/settings.json` → click connect → enter password. You can now run `.sql` files with `Ctrl+E Ctrl+E` and see results in a tab. You'll use this in Phase 5 for `sql/validation.sql`.

### 1.6 Day-to-day

```bash
docker compose stop      # pause, keeps data
docker compose start     # resume
docker compose down      # remove container, keeps data volume
docker compose down -v   # nuke everything incl. data (fresh start)
```

**✅ Done when:** `docker compose ps` says healthy and you got a `mysql>` prompt.

---

## Phase 2 — Look at the data yourself (≈45 min)

Don't skip. You need to *see* the traps, not read about them, or the writeup will sound borrowed.

In `scratch/explore.py`:

- [ ] Cell: read the three xlsx into `pbp`, `pbpp`, `ros` with `pd.read_excel`.
- [ ] Cell: `pbp.play_event.value_counts()` — see the 15 event types.
- [ ] Cell: `pbp[pbp.play_id == 1]` — the Starting Lineup. 10 rows, one play_id. **Note:** this is why `pbp.play_id` is not unique and why your output should have play_id 1 *once*.
- [ ] Cell: `pbpp[pbpp.play_event == 'Substitution'].head(10)` — confirm `sequence` 1 = in, 2 = out. Read the `play_text`.
- [ ] Cell: game `1947160`, `pbp[pbp.play_id.between(110, 125)]` — watch Q1 end and Q2 start. **Notice: no substitution rows at 12:00.** New players just… appear. This is the whole problem.
- [ ] Cell: find Devin Booker (`player_id 845564`) in `pbpp`. Look at his `team_abbr` on `play_id 149`. Then look him up in `ros`. → Trap 1.
- [ ] Cell: `pbpp[pbpp.play_detail == 'Technical']` → T.J. Warren, play 393. Ask yourself: was he on the floor? (He wasn't.) → Trap 2.
- [ ] Cell: `pbpp[pbpp.play_event == 'Foul'].groupby('sequence').size()` → 1 = committer, 3 = fouled.

**✅ Done when:** you can explain both traps out loud without looking at notes.

---

## Phase 3 — `on_court.py`: load → openers (≈2–3 hrs)

Create `on_court.py`. Build top-down, one `# %%` section at a time. After each function, run its cell and *look at the return value* in the Interactive Window before writing the next.

### 3.1 Section 1 — imports + config

```
# %% 1. imports + config
imports: argparse, os, pandas, mysql.connector, dotenv
load_dotenv()
DATA_DIR = "data"
constants: SUB_IN = 1, SUB_OUT = 2, STARTING_LINEUP_PLAY_ID = 1
```

### 3.2 Section 2 — `load()`

```
def load(data_dir) -> tuple[DataFrame, DataFrame, DataFrame]:
    read pbp.xlsx, pbp-players.xlsx, rosters.xlsx
    cast id columns to int (they come in as float because of NaNs elsewhere)
    return pbp, pbp_players, rosters
```

Gotcha: `player_id`, `team_id`, `event_id`, `play_id` load as `float64`. Cast early with `.astype(int)` on the columns that have no NaNs, or you'll be comparing `2.0 == 2` all day.

- [ ] Run cell. `pbp.shape == (1011, 30)`, `pbpp.shape == (1357, 38)`, `ros.shape == (66, 12)`.

### 3.3 Section 3 — `player_team_map()`

```
def player_team_map(rosters) -> dict[(event_id, player_id) -> team_id]:
    one line-ish. rosters is authoritative. never use pbp_players.team_id.
```

Also useful, same section: a `home_team(pbp)` helper → `{event_id: home_team_id}` for the `is_home` column later.

- [ ] Run. `len(map) == 66`. `map[(1947312, 845564)]` → Phoenix's team_id (21), not Houston's.

### 3.4 Section 4 — `period_openers()` — **the hard part**

```
def period_openers(pbp_players, team_map) -> dict[(event_id, period, team_id) -> set[player_id]]:
    result = {}
    for each (event_id, period) group, sorted by (play_id, play_sequence):
        if period == 1:
            starters = rows where play_id == 1  -> group player_ids by team via team_map
        else:
            subbed_in  = {team: set()}
            openers    = {team: set()}
            for each row in order:
                team = team_map[(event_id, player_id)]      # TRAP 1: not row.team_id
                if row is Substitution:
                    if row.sequence == SUB_IN:  subbed_in[team].add(player)
                    if row.sequence == SUB_OUT and player not in subbed_in[team]:
                        openers[team].add(player)
                else:
                    if row.play_detail == 'Technical': continue   # TRAP 2
                    if player not in subbed_in[team]:
                        openers[team].add(player)
        result[(event_id, period, team)] = openers[team]  for each team
    return result
```

Also skip `Start Period` / `End Period` / `Timeout` rows as evidence — they carry a player_id but it's not meaningful. Check what `pbpp[pbpp.play_event == 'Timeout']` looks like before deciding.

- [ ] Run. **Every one of the 16 keys should have exactly 5 players.** Print `{k: len(v) for k, v in openers.items()}`. If any says 6, you missed a trap. If any says 4, you dropped a valid evidence type.
- [ ] Sanity spot-check vs what I saw: game `1947160` Q2 BOS opener includes Baynes + Smart; GS opener includes Thompson + West.
- [ ] Self-test idea (great for the writeup): run the *back-solve* branch on period 1 too, compare to the given Starting Lineup. They should match. Proves the rule works where you have ground truth.

**✅ Done when:** 16 keys, all length 5.

---

## Phase 4 — `on_court.py`: walk → long → validate (≈1.5 hrs)

### 4.1 Section 5 — `walk_plays()`

```
def walk_plays(pbp, pbp_players, openers, team_map) -> dict[(event_id, play_id) -> dict[team_id -> set[player_id]]]:
    subs = pbp_players rows where Substitution, sorted, grouped by (event_id, play_id)
    plays = pbp[[event_id, play_id, period]].drop_duplicates().sort_values([event_id, play_id])
    for each event_id:
        on_court = None
        for each play in order:
            if period changed (or first play):
                on_court = deep copy of openers for this (event_id, period, each team)
            if play_id has substitution rows:
                for each sub pair: on_court[team].remove(out); on_court[team].add(in)
            result[(event_id, play_id)] = copy of on_court   # copy! sets are mutable
    return result
```

Gotchas:
- **Copy the sets** when you store them, or every play will point at the same mutating object and your whole table will show the final lineup.
- If `.remove(out)` raises `KeyError`, that's a *good* error — it means your model says a player left who wasn't on. Let it raise during dev; it's your bug detector. In the final version, catch it and log the play_id.
- Sub takes effect on its own play row (decided). Say so in the walkthrough.

- [ ] Run. `len(result) == 993`. Every value: 2 teams × 5 players.

### 4.2 Section 6 — `to_long()`

```
def to_long(on_court, pbp, team_map, home_map) -> DataFrame:
    rows = []
    for (event_id, play_id), teams in on_court.items():
        for team_id, players in teams.items():
            for player_id in players:
                rows.append((event_id, play_id, player_id, team_id, period, is_home))
    return DataFrame(rows, columns=[...])
```

Get `period` from a `{(event_id, play_id): period}` lookup built off `pbp`.

- [ ] Run. `df.shape[0] == 9930`. `df.groupby(['event_id','play_id']).size().eq(10).all()`.

### 4.3 Section 7 — `validate()`

```
def validate(df, pbp, rosters) -> None:   # raise AssertionError with a message on failure
    1. set(pbp.play_id per event) == set(df.play_id per event)         # every play represented
    2. every (event_id, play_id) has exactly 10 rows
    3. every (event_id, play_id, team_id) has exactly 5 rows
    4. every (event_id, player_id) in df exists in rosters
    5. no (event_id, play_id, player_id) duplicated
    print a short "all N checks passed" line
```

- [ ] Run on your frame. Passes.
- [ ] Break it on purpose (drop a row) → it fails with a readable message. Fix it back.

### 4.4 `test_on_court.py` (≈30 min)

Small. 4–6 tests. Import functions from `on_court`. Ideas:
- `period_openers` returns 16 keys, all size 5 (uses real data — fine, it's fixture data)
- `player_team_map` puts Booker on Phoenix
- `to_long` yields 9,930 rows
- a tiny hand-built 3-play DataFrame where you know the answer, to test `walk_plays` sub logic in isolation

```bash
pytest -q
```

**✅ Done when:** `validate()` passes, `pytest` green.

---

## Phase 5 — MySQL write + dump + your own analysis (≈1.5 hrs)

### 5.1 Section 8 — `write_mysql()`

```
DDL = """CREATE TABLE IF NOT EXISTS pbp_players_on_court ( ...from CLAUDE.md... )"""

def get_conn():
    mysql.connector.connect(host=, port=, user=, password=, database=)  # all from os.environ

def write_mysql(df, conn):
    cur = conn.cursor()
    cur.execute(DDL)
    for event_id in df.event_id.unique():
        rows = df[df.event_id == event_id]
        cur.execute("DELETE FROM pbp_players_on_court WHERE event_id = %s", (event_id,))
        cur.executemany(
            "INSERT INTO pbp_players_on_court (event_id, play_id, player_id, team_id, period, is_home) VALUES (%s,%s,%s,%s,%s,%s)",
            list_of_tuples_of_PYTHON_INTS,
        )
    conn.commit()     # one commit -> all games or none
```

Gotchas:
- **numpy ints are rejected by mysql-connector.** `TypeError: Failed processing format-parameters`. Convert every value to plain `int()` when you build the tuples. `df.astype(int).itertuples(index=False, name=None)` → then `[tuple(int(x) for x in t) for t in ...]`, or `df.to_numpy().tolist()` after `astype(object)`. Pick one.
- Wrap in `try / except → conn.rollback(); raise`. Then the "second run updates" requirement is trivially true and provably atomic.
- `executemany` batches ~10k rows in one round trip on this connector. Fine. Mention in complexity section.

### 5.2 Section 9 — `main()` + argparse

```
parser: --game  (required)  "all" or an event_id
        --validate  (flag)
        --no-db     (flag, optional: build + validate without writing — handy for dev)
main():
    pbp, pbpp, ros = load()
    if game != "all": filter all three frames to that event_id  (error if not found)
    ... pipeline ...
    if validate: validate(df, ...)
    if not no_db: write_mysql(df, get_conn())
if __name__ == "__main__": main()
```

- [ ] Run `python on_court.py --game 1947160`. Then in `docker exec -it swish-mysql mysql -u swish -p swish`:

```sql
SELECT COUNT(*) FROM pbp_players_on_court;           -- 4890
SELECT event_id, COUNT(*) FROM pbp_players_on_court GROUP BY event_id;
```

- [ ] Run `python on_court.py --game all`. Count → 9930.
- [ ] Run `--game all` **again**. Count still 9930 (not 19860). That's your idempotency proof. Screenshot or paste into the walkthrough.
- [ ] Run `--game 999`. Clean error message, not a stack trace.

### 5.3 `sql/validation.sql` — the "do your own calculations" tip

Write the query the prompt hints at: **team points scored while each player was on court.** Shape:

```
SELECT oc.event_id, oc.player_id, oc.team_id,
       SUM(CASE WHEN p.play_team_id = oc.team_id THEN p.points_scored ELSE 0 END) AS pts_for,
       SUM(CASE WHEN p.play_team_id <> oc.team_id THEN p.points_scored ELSE 0 END) AS pts_against,
       COUNT(*) AS plays_on_court
FROM pbp_players_on_court oc
JOIN pbp p ON p.event_id = oc.event_id AND p.play_id = oc.play_id   -- pbp needs to be in MySQL too, see below
GROUP BY ...
```

Two ways to get `pbp` into MySQL for the join:
- (a) quick: in the mysql shell, `CREATE TABLE pbp (...)` then load from a CSV you export from pandas — fiddly on Windows.
- (b) **easier:** add an optional `--load-source` flag to `on_court.py` that `to_sql`s the three input frames into `pbp`, `pbp_players`, `rosters` tables (pandas `to_sql` needs `sqlalchemy` — add to requirements if you go this way; or write a small executemany like 5.1). Say in the walkthrough this is a dev convenience, not part of the deliverable table.

Then the killer check — **sum of `pts_for` across a team's 5 on-court players per play == 5 × team total.** Equivalent: for each team, `SUM(points_scored)` from `pbp` should equal `SUM(pts_for) / 5` from your table. If it matches, your lineups are internally consistent with the scoring. Put the numbers in the walkthrough.

- [ ] Query runs. Numbers reconcile.

### 5.4 The dump deliverable

Run `mysqldump` inside the container, write to a file inside the container, copy it out. This sidesteps PowerShell's redirect-encoding weirdness entirely.

```bash
docker exec swish-mysql sh -c "mysqldump -u root -p\$MYSQL_ROOT_PASSWORD swish pbp_players_on_court --result-file=/tmp/dump.sql"
```
```bash
docker cp swish-mysql:/tmp/dump.sql sql/pbp_players_on_court.sql
```

- [ ] Open `sql/pbp_players_on_court.sql`. Has `CREATE TABLE` and `INSERT INTO` lines. ~9,930 values. Roughly 400–600 KB.
- [ ] **Prove it restores.** In the mysql shell: `CREATE DATABASE swish_check;` then

```bash
docker exec swish-mysql sh -c "mysql -u root -p\$MYSQL_ROOT_PASSWORD swish_check < /tmp/dump.sql"
```

then `SELECT COUNT(*) FROM swish_check.pbp_players_on_court;` → 9930. Drop `swish_check` after.

**✅ Done when:** rerun is idempotent, dump restores, points reconcile.

---

## Phase 6 — Part 1 writeup: `docs/walkthrough.md` (≈1.5 hrs)

Outline is already in the file. What goes under each heading — **your words**, but hit these beats:

- **Problem** — 3 sentences. Boxscore gap, need lineups, no lineup feed.
- **Why one script, sectioned** — prompt says "script"; ~300 lines; each section is a pure function so it's testable and it mirrors the stages a prod pipeline would split into (→ Part 2).
- **Data flow** — the 6-function chain. A small ASCII arrow diagram is fine.
- **Period openers** — this is the centerpiece. Explain: no subs at breaks → back-solve → the two evidence rules → **the two traps with the exact play_ids** → 16/16 resolve to 5 → the P1 self-test.
- **Why long grain** — 10 rows/play joins straight to `pbp`; the prompt's "sum points while on court" is one `JOIN … GROUP BY`. Wide (10 columns) would need a 10-way UNION for every question.
- **Denormalized columns** — `team_id`, `period`, `is_home` cost ~nothing and save a join in the common query.
- **Idempotency** — delete-then-insert per game in one txn. Why not upsert: orphans if a play is corrected away upstream. Paste the "ran twice, still 9930" proof.
- **Validation** — list the 5 checks + the points reconciliation with real numbers.
- **Time complexity** — sort `O(N log N)`, N = pbp_players rows; one linear pass `O(N)`; output `O(10·P)`, P = plays. Per game, independent → parallel across games. DB write is one batched round trip per game. Memory `O(N)`: whole game in RAM, fine (a game is ~500 plays; even a full season × 1,230 games is ~600k plays).
- **Shortcomings** — be honest, this section is graded:
  - openers rule fails if a player is on the floor an entire period and never touches the ball / commits a foul / rebounds (rare but real: end-of-blowout benchwarmers). Fallback you'd add: prior-period closers, then roster minutes.
  - relies on the feed's `sequence` semantics for subs; would validate against `play_text` parsing in prod.
  - no OT data to test against; code handles period ≥ 5 but unverified.
  - `pbp_players.team_abbr` is provably unreliable (1 row); rosters could be too — no independent check.
  - ejections / injuries with no sub event would break the 5-count; today it raises.
- **If I had more time** — stint table, per-lineup plus/minus, unit tests on synthetic edge cases.

---

## Phase 7 — Part 2: diagram + `docs/system-design.md` (≈2–3 hrs)

### 7.1 Decide the architecture first (paper, 20 min)

Prompt asks specifically: **ingest**, **when does the code run**, **storage**, **serving**, **scaling**, **why these tools**. A defensible, not-overbuilt answer for a sports-analytics shop:

```
[Data provider pbp REST API]
        │  poll (schedule-aware: every ~10s during live games, hourly otherwise; backfill on demand)
        ▼
[Ingestion service]  ── writes raw JSON ──▶ [Object storage / raw landing]   (S3 or equivalent; immutable, replayable)
        │  normalizes → upserts
        ▼
[MySQL: pbp, pbp_players, rosters]
        │  emits "game N has new plays" (queue message, or watermark table)
        ▼
[Orchestrator]  (Airflow / Prefect / even cron+lock for v1)  ── triggers per game ──▶ [on_court job]  (containerized on_court.py, --game N)
                                                                                            │  delete+insert txn
                                                                                            ▼
                                                                          [MySQL: pbp_players_on_court]  ──▶ read replica ──▶ [BI / analysts / internal API]
                                          [Monitoring: run status, lineup≠10 alerts, freshness]
```

Key talking points, one paragraph each:
- **Ingest:** poll vs webhook (you only have REST → poll). Schedule API tells you *when* games are live so you don't hammer the API at 4 am. Store raw before transforming — replay is your undo button.
- **Trigger:** event-driven per game ("new pbp rows for game N landed → run for game N"). Your `--game` flag is exactly the unit of work. Idempotent job = safe to retrigger on every batch.
- **Storage:** MySQL is required by Part 1 and fine at this volume (~600k plays/season, ~6M on-court rows). Partition by season. Raw JSON to object storage. Mention when you'd outgrow it (warehouse: BigQuery/Snowflake for analyst queries across seasons).
- **Serving:** read replica for analysts / BI; thin internal API if product needs it. Don't let dashboards hit the write DB.
- **Scaling:** games are independent → N workers. Bottleneck is API rate limits, not compute. Backfill = enqueue every game_id. Late corrections from the provider = same path, idempotent rerun.
- **Tools & alternatives:** why containers + orchestrator over a cron on a VM (visibility, retries); why not Kafka yet (volume doesn't justify; a queue or DB watermark suffices); cloud-agnostic or pick one (AWS: ECS/Fargate + S3 + RDS MySQL + EventBridge/MWAA is the boring good answer).
- **Failure modes:** API down → backoff, stale-data alert; lineup≠10 → job fails loudly, quarantine game, alert; provider corrects a play → rerun game.

### 7.2 Build the diagram in VS Code (≈1.5 hrs)

Draw.io Integration extension is installed (Phase 0).

- [ ] Create file `docs/system-design.drawio.png`. **The `.drawio.png` double extension matters:** the extension stores the diagram *inside* the PNG, so the one file is both editable in VS Code and a normal image everyone can open. No export step. `docs/system-design.md` already embeds it.
- [ ] Click the file → draw.io editor opens in the tab.
- [ ] Left panel → `+ More Shapes` → enable **AWS 4** (or GCP/Azure if you pick those) and **Flowchart**. Gives you real service icons.
- [ ] Layout left → right: source on the left, consumers on the right. Same reading order as their example diagram.
- [ ] Group the "your system" boundary with a dashed rounded rectangle — mirrors their example, signals what you own vs external.
- [ ] Label every arrow with *what* flows (raw JSON, upsert, trigger msg, SQL). Unlabeled arrows are the #1 weak diagram tell.
- [ ] Add a small "monitoring / alerting" box off to the side with dotted lines to the job and the DB.
- [ ] Keep to ~10–12 boxes. If you need more, you're overbuilding.
- [ ] Save (`Ctrl+S`). Open the `.md` preview (`Ctrl+Shift+V`) → image renders.

### 7.3 Write `docs/system-design.md`

Outline is in the file. One paragraph per heading, using 7.1. Reference the diagram's box names so the reader can follow along. ~800–1,200 words.

---

## Phase 8 — Package & submit (≈45 min)

### 8.1 Fresh-clone test

Prove it runs for a stranger.

- [ ] `git clone` your repo into a temp folder (or copy the folder without `.venv`/`.env`).
- [ ] New venv, `pip install -r requirements.txt`, copy `.env.example` → `.env`, fill passwords, `docker compose up -d`, `python on_court.py --game all --validate`. Works? Good.

### 8.2 Secrets sweep

- [ ] `.env` is not in the zip. `grep -ri password` over the folder → only `.env.example` placeholders and `docker-compose.yml` variable refs.
- [ ] `sql/pbp_players_on_court.sql` has no `-- Host:` line with a real hostname you care about (it'll say `localhost`; fine).

### 8.3 What goes in the zip

```
swish-de-take-home-chris-boone.zip
├─ README.md
├─ on_court.py
├─ test_on_court.py
├─ requirements.txt
├─ docker-compose.yml
├─ .env.example
├─ data/  (3 xlsx — include, so it runs standalone)
├─ sql/pbp_players_on_court.sql
├─ sql/validation.sql
└─ docs/walkthrough.md
   docs/system-design.md
   docs/system-design.drawio.png
```

Leave out: `.git`, `.venv`, `.env`, `scratch/`, `.vscode/`, `CLAUDE.md`, `docs/plan.md`, `docs/swish-de-take-home.pdf`, `__pycache__`.

- [ ] Zip built. Unzipped into a clean folder, README instructions followed, everything runs.
- [ ] Final read of both `.md` files out loud. Cut anything you can't defend in an interview.

**✅ Done when:** zip runs from scratch on a machine (or folder) that has never seen the repo.

---

## Time budget

| Phase | est. |
|---|---|
| 0–1 setup | 1 hr |
| 2 explore | 45 min |
| 3 load→openers | 2–3 hrs |
| 4 walk→validate + tests | 2 hrs |
| 5 MySQL + dump + analysis | 1.5 hrs |
| 6 walkthrough | 1.5 hrs |
| 7 diagram + design doc | 2–3 hrs |
| 8 package | 45 min |
| **total** | **~12–14 hrs** |

Phase 3.4 is where the time goes. Everything after it is mechanical.
