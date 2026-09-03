# Step-by-step plan

Your roadmap. Check boxes as you go. Each phase ends with a **✅ Done when**
gate — don't move on until it's true. Phases 0–2 are setup; 3–5 are the code;
6–7 are the writeups; 8 is packaging.

Ground rule for Claude in this repo: you write the code, Claude guides.
The **Skeleton** folds are concrete Python with the real library calls — but
they're skeletons, not the file. You type them in, run them cell by cell, fix
what breaks, and rename/restructure as you see fit.


## What the PDF actually asks for

Every phase and step below carries a tag with the requirement it serves (e.g. R3). Anything
tagged **optional** is my addition — useful, not required. Skip it on a time
crunch and nothing in the deliverable breaks.

**Part 1 — code** (`docs/swish-de-take-home.pdf`, page 1–2)

| tag | requirement, as written |
|---|---|
| R1 | script written in Python |
| R2 | each `play_id` from `pbp` must be represented in the new data set |
| R3 | for each `play_id`, exactly 10 players selected as on court |
| R4 | script writes the data set to a MySQL table `pbp_players_on_court` |
| R5 | run a second time → updates the table to catch changes |
| R6 | argument to run one game or all games |
| R7 | deliver the script; remove private connection parameters |
| R8 | deliver a MySQL export: CREATE statement + the data |
| R9 | deliver a written walkthrough: why this structure, shortcomings, time complexity |
| T1 | *tip:* design for analysis (e.g. sum team points while each player was on court); try your own calculations on it |
| T2 | *tip:* the script accesses only the 3 provided data sets |

**Part 2 — system design**

| tag | requirement, as written |
|---|---|
| R10 | system diagram (draw.io or similar) |
| R11 | writeup: your decisions, why those tools, how it scales; end-to-end from ingest to serving; how the code knows when to run; storage strategy |

**Where the difficulty actually is:** R3. Q2–Q4 opening lineups aren't in the
data and have to be inferred (Phase 3.4). Everything else is plumbing.

**What's optional:** all of Phase 2 (understanding, not code), 3.4d, 4.4, 5.3.
Phase 2 exists so you can defend the algorithm in the follow-up interview, not
because the PDF asks for it.

---

## Phase 0 — Environment (≈30 min) [→ R1, R4 — setup]

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

## Phase 1 — MySQL in Docker (≈30 min, first time) [→ R4, R8 — setup]

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

## Phase 2 — Look at the data yourself (≈45 min) [→ optional — understanding only; every fact here is already in CLAUDE.md]

Don't skip. You need to *see* the traps, not read about them, or the writeup will sound borrowed.

In `scratch/explore.py`, one `# %%` cell per step. Each step says **Do** (the exact
operation), **Why** (what it teaches you / what it feeds later), and **Expect**
(what the output should look like). Write the code from **Do** first; open
**Hint** if you're not sure which pandas call, **Example** if you're stuck.
Scratch code isn't a deliverable, so the Phase 2 examples are complete —
from Phase 3 on they're **Skeleton** folds: concrete Python you type in yourself.

### Reference: what `sequence` means per event type

You'll need this all through Phases 2–4. Verified against the data.

| `play_event` | `sequence=1` | `sequence=2` | `sequence=3` |
|---|---|---|---|
| Substitution | player coming **IN** | player going **OUT** | — |
| Foul | committed the foul | — | player who was fouled |
| Field Goal Made | shooter | assister | — |
| Field Goal Missed | shooter | — | blocker |
| Turnover | player who turned it over | — | player who stole it |
| Jump Ball | jumper | gained possession | other jumper |
| Rebound / Free Throw / Violation | the player | — | — |

Rows with `player_id = NaN` exist for team events (timeouts, period start/end, team rebounds, delay-of-game). They aren't people. Filter them out everywhere.

---

### 2.0 Setup cell [→ optional]

**Do:** import pandas, widen the display so frames don't truncate columns.
**Why:** `pbp` has 30 columns, `pbpp` has 38. Default display hides most of them.

<details><summary>Example</summary>

```python
# %% setup
import pandas as pd
pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 50)
pd.set_option("display.max_rows", 200)
```

</details>

---

- [ ] **2.1 Load the three workbooks** [→ optional — context for 3.2]

**Do:** Read `data/pbp.xlsx`, `data/pbp-players.xlsx`, `data/rosters.xlsx` into three DataFrames named `pbp`, `pbpp`, `ros`. Print the `.shape` of each. Then print `pbp.dtypes` and look at the type of every `*_id` column.
**Why:** Confirms paths resolve from the repo root, and shows you that every id column loads as `float64` (pandas does this whenever a column has any NaN). That's the cast you'll do in Phase 3.2.
**Expect:** `(1011, 30)`, `(1357, 38)`, `(66, 12)`. Ids are `float64`.

<details><summary>Hint</summary>

`pd.read_excel(path)` — one call per file, openpyxl is picked up automatically. Paths are relative to the repo root because `.vscode/settings.json` pins `jupyter.notebookFileRoot` to the workspace. If you get `FileNotFoundError`, **close the Interactive Window tab** and `Shift+Enter` again (the root is fixed when the window is created — restarting the kernel isn't enough). Check `import os; os.getcwd()`.

</details>
<details><summary>Example</summary>

```python
# %% 2.1 load
pbp  = pd.read_excel("data/pbp.xlsx")
pbpp = pd.read_excel("data/pbp-players.xlsx")
ros  = pd.read_excel("data/rosters.xlsx")
print(pbp.shape, pbpp.shape, ros.shape)
pbp.dtypes
```

Type `pbp` alone in a cell → scrollable table.

</details>

---

- [ ] **2.2 Inventory the event types** [→ optional — orientation only]

**Do:** Count rows in `pbp` by `play_event`, including NaN. Then group by both `play_event_id` and `play_event` to see the id→name mapping. Then do the same count on `pbpp` and compare — which events have *more* rows in `pbpp` than in `pbp`, and why?
**Why:** You need to know which events are "a player did something on the floor" (evidence) vs. bookkeeping (Substitution, Start/End Period, Timeout). The `pbpp` vs `pbp` row difference is your first look at multi-player plays (assists, blocks, steals, fouls).
**Expect:** 15 named types + 20 NaN rows in `pbp`. `Substitution` = 104 in `pbp`, 208 in `pbpp`. `Foul` = 83 vs 164. `Field Goal Made` = 149 vs 241.

<details><summary>Hint</summary>

`Series.value_counts(dropna=False)` for the first. `DataFrame.groupby([...], dropna=False).size()` for the id mapping. For the comparison, `pd.concat([pbp_counts, pbpp_counts], axis=1)` puts them side by side.

</details>
<details><summary>Example</summary>

```python
# %% 2.2 event types
pbp.play_event.value_counts(dropna=False)
```
```python
pbp.groupby(["play_event_id", "play_event"], dropna=False).size()
```
```python
pd.concat([pbp.play_event.value_counts().rename("pbp"),
           pbpp.play_event.value_counts().rename("pbpp")], axis=1)
```

</details>

---

- [ ] **2.3 Find out why `play_id` isn't unique** [→ context for 3.4a + 4.1a]

**Do:** Per `event_id`, compute the number of rows and the number of distinct `play_id`s in `pbp`. Then pull every `pbp` row where `play_id == 1` and show `event_id, play_id, play_sequence, play_team_id, play_text`. Then do the same for `pbpp` and add `player_id, first_name, last_name, team_abbr`.
**Why:** `play_id 1` is "Starting Lineup" — 10 rows sharing one id, one per starter. In `pbp` those rows only carry a team; in `pbpp` they carry the actual players. Two consequences: (1) your output must emit `play_id 1` **once** with 10 players, so you'll `drop_duplicates` on `(event_id, play_id)` when building your play list; (2) the Q1 starters are handed to you for free.
**Expect:** `count − nunique == 9` for each game (498 vs 489, 513 vs 504). 10 rows per game at `play_id 1`, five per team, `play_sequence` 1–10.

<details><summary>Hint</summary>

`pbp.groupby("event_id").play_id.agg(["count", "nunique"])`. Then boolean filter `pbp[pbp.play_id == 1]` and select columns with a list inside `[]`.

</details>
<details><summary>Example</summary>

```python
# %% 2.3 starting lineup
pbp.groupby("event_id").play_id.agg(["count", "nunique"])
```
```python
pbp[pbp.play_id == 1][["event_id", "play_id", "play_sequence", "play_team_id", "play_text"]]
```
```python
pbpp[pbpp.play_id == 1][["event_id", "player_id", "first_name", "last_name", "team_abbr", "position_abbr"]]
```

</details>

---

- [ ] **2.4 Decode substitution rows** [→ context for 3.4b + 4.1b]

**Do:** Filter `pbpp` to `play_event == "Substitution"`. Show the first 10 rows with `play_id, sequence, first_name, last_name, team_abbr, play_text`. Read the `play_text` ("X in for Y") against the name on each `sequence` value and decide which number means IN and which means OUT. Then confirm every substitution has exactly 2 rows: group by `(event_id, play_id)`, `.size()`, then `.value_counts()` on that.
**Why:** This is the state change your Phase 4 loop applies. If you get IN/OUT backwards, every lineup after the first sub is wrong.
**Expect:** `sequence 1` = IN, `sequence 2` = OUT. `value_counts` shows `{2: 104}` — never 1, never 3.

<details><summary>Hint</summary>

Save the filtered frame as `subs` — you'll reuse it in 2.5. `subs.groupby(["event_id", "play_id"]).size().value_counts()` gives the distribution of rows-per-sub.

</details>
<details><summary>Example</summary>

```python
# %% 2.4 substitutions
subs = pbpp[pbpp.play_event == "Substitution"]
subs[["event_id", "play_id", "sequence", "first_name", "last_name", "team_abbr", "play_text"]].head(10)
```
```python
subs.groupby(["event_id", "play_id"]).size().value_counts()
```

</details>

---

- [ ] **2.5 Watch a period boundary — this is the whole problem** [→ context for 3.4 — the core problem]

**Do:** Filter `pbp` to game `1947160`, plays 110–125. Show `play_id, period, clock_minutes, clock_seconds, play_event, play_team_id, play_text`. Read it top to bottom: who's involved in the last few Q1 plays, then who's involved in the first few Q2 plays. Then, across the **whole** `subs` frame, filter to `clock_minutes == 12 and clock_seconds == 0` — any subs recorded at the start of a period?
**Why:** Q2 opens with Baynes and Smart doing things for BOS, Thompson and West for GS — none of them were subbed in. Between periods, the feed records **no substitutions**. So the Q1 closing lineup ≠ the Q2 opening lineup, and nothing tells you the new five. You have to infer them. That inference is `period_openers()` in Phase 3.4 and it's the heart of the take-home.
**Expect:** Q1's last plays involve Theis, Rozier, Brown, McGee, Young. Q2's first plays involve Baynes, Smart, Thompson, West. The 12:00 filter returns an **empty** frame.

<details><summary>Hint</summary>

`Series.between(110, 125)` is cleaner than two comparisons. For the second check, combine two boolean conditions with `&` and wrap each in parentheses.

</details>
<details><summary>Example</summary>

```python
# %% 2.5 period boundary
g = pbp[pbp.event_id == 1947160]
g[g.play_id.between(110, 125)][["play_id", "period", "clock_minutes", "clock_seconds", "play_event", "play_team_id", "play_text"]]
```
```python
subs[(subs.clock_minutes == 12) & (subs.clock_seconds == 0)]      # empty
```

</details>

---

- [ ] **2.6 Trap 1 — prove `pbpp.team_abbr` is unreliable** [→ context for Trap 1 → R3]

**Do:** Build a lookup from `ros`: index by `(event_id, player_id)`, value `team_abbr`. Join it onto `pbpp` as a new column `roster_team`. Filter to rows where `team_abbr != roster_team` (ignoring NaN player rows). Show `play_id, first_name, last_name, team_abbr, roster_team, play_text`. Then also count how many `pbpp` players have **no** roster match.
**Why:** Exactly one row disagrees — Devin Booker (Phoenix) tagged `Hou` on `play_id 149`. One bad row is enough to put a Suns player in Houston's Q2 opening five and give you 6 players. Rule for the rest of the project: **team comes from `rosters`, never from `pbpp.team_id`/`team_abbr`.** The zero-unmatched check tells you rosters are complete enough to be the authority.
**Expect:** One mismatched row (Booker, `play_id 149`, game `1947312`). Zero unmatched players.

<details><summary>Hint</summary>

`ros.set_index(["event_id", "player_id"]).team_abbr` gives a Series with a 2-level index. `pbpp.join(that_series.rename("roster_team"), on=["event_id", "player_id"])` aligns on those two columns. Then `chk[chk.team_abbr != chk.roster_team]` — but drop rows where `player_id` is NaN first or they'll show up as false mismatches. `chk.roster_team.isna().sum()` for the unmatched count (after dropping NaN players).

</details>
<details><summary>Example</summary>

```python
# %% 2.6 trap 1: team attribution
team_lookup = ros.set_index(["event_id", "player_id"]).team_abbr
chk = pbpp[pbpp.player_id.notna()].join(team_lookup.rename("roster_team"), on=["event_id", "player_id"])
chk[chk.team_abbr != chk.roster_team][["play_id", "first_name", "last_name", "team_abbr", "roster_team", "play_text"]]
```
```python
chk.roster_team.isna().sum()     # 0 → every pbpp player is on a roster
```

</details>

---

- [ ] **2.7 Trap 2 — prove technical fouls come from the bench** [→ context for Trap 2 → R3]

**Do:** Filter `pbpp` to `play_detail == "Technical"`. Note the player and play. Then pull **everything** that player did in that game and period — all events, subs included — and read it. Was he subbed in? Subbed out? Did he do anything besides the technical?
**Why:** T.J. Warren's only Q4 appearance is the technical at `play_id 393`. He's never subbed in or out in Q4. If you treat a technical as evidence of being on the floor, Phoenix's Q4 opening five becomes six. Technicals can be assessed to bench players (and coaches). Rule: **`play_detail == "Technical"` is not on-court evidence.**
**Expect:** One row: Warren (`player_id 660085`), game `1947312`, `play_id 393`, period 4. His Q4 history is that single row.

<details><summary>Hint</summary>

Two filters. The second combines three conditions with `&`: `player_id == 660085`, `event_id == 1947312`, `period == 4`.

</details>
<details><summary>Example</summary>

```python
# %% 2.7 trap 2: technical fouls
pbpp[pbpp.play_detail == "Technical"][["event_id", "play_id", "period", "first_name", "last_name", "team_abbr", "play_text"]]
```
```python
w = pbpp[(pbpp.player_id == 660085) & (pbpp.event_id == 1947312) & (pbpp.period == 4)]
w[["play_id", "clock_minutes", "clock_seconds", "play_event", "sequence", "play_text"]]
```

</details>

---

- [ ] **2.8 Confirm the `sequence` table above** [→ optional — verifies the table above]

**Do:** For each of `Foul`, `Field Goal Made`, `Field Goal Missed`, `Turnover`, `Jump Ball`: filter `pbpp`, group by `sequence`, `.size()`. Then for `Foul` and `Turnover`, show 6 rows of `play_id, sequence, last_name, play_text` and check which sequence's name matches the actor in the text.
**Why:** In Phase 3.4, every non-sub row with a real `player_id` is evidence that player was on the floor — regardless of sequence. But you need to *know* that's true (e.g. that `sequence=3` on a Foul is the fouled player, not a bench guy) to defend it in the writeup.
**Expect:** Matches the reference table at the top of this phase. `Foul`: 83 at seq 1, 81 at seq 3 (two fouls had no drawn-by player — a technical and an illegal defense).

<details><summary>Hint</summary>

`pbpp.groupby(["play_event", "sequence"]).size()` does all event types in one shot. Then eyeball a few rows per type.

</details>
<details><summary>Example</summary>

```python
# %% 2.8 sequence semantics
pbpp.groupby(["play_event", "sequence"]).size()
```
```python
pbpp[pbpp.play_event == "Foul"][["play_id", "sequence", "last_name", "play_text"]].head(6)
```
```python
pbpp[pbpp.play_event == "Turnover"][["play_id", "sequence", "last_name", "play_text"]].head(6)
```

</details>

---

**✅ Done when:** you can explain both traps out loud without notes, and you can say in one sentence why Q2 openers have to be inferred.

---

## Phase 3 — `on_court.py`: load → openers (≈2–3 hrs) [→ R1, R3]

Create `on_court.py` at the repo root. Build top-down, one `# %%` section at a
time. After each function: run its cell, call it, **look at the return value**
before writing the next one. Folds from here on are **Hint** (which tools /
what to watch for) and **Skeleton** (a concrete Python skeleton with the real
pandas / mysql calls — type it, run it, make it yours). You write the file.

---

### 3.1 Section 1 — imports + config [→ R1]

- [ ] **Do:** Imports (`argparse`, `os`, `sys`, `pandas`, `mysql.connector`, `from dotenv import load_dotenv`). Call `load_dotenv()` at module level so `.env` is read on import. Define constants you'll reference by name instead of magic numbers: `DATA_DIR = "data"`, `SUB_IN = 1`, `SUB_OUT = 2`, `STARTING_LINEUP_PLAY_ID = 1`, `PLAYERS_PER_TEAM = 5`, `TECHNICAL = "Technical"`.
**Why:** Constants make the algorithm readable in the writeup ("if `sequence == SUB_IN`" vs "if `sequence == 1`"), and one place to change if the feed's conventions differ.

---

### 3.2 Section 2 — `load()` [→ R1, T2]

- [ ] **Do:** Write `load(data_dir=DATA_DIR)` returning `(pbp, pbp_players, rosters)`. Read the three files. For each frame, cast the id columns that are never NaN to `int`: `event_id, play_id, play_sequence, period` everywhere; `home_team_id, away_team_id, play_team_id` in `pbp`; `team_id, player_id` in `rosters`. In `pbp_players`, `player_id` and `team_id` *are* NaN on team-event rows — drop those rows (`player_id.notna()`) then cast. Sort every frame by `(event_id, play_id, play_sequence)` — `rosters` has no play columns, sort by `(event_id, team_id, player_id)`.
**Why:** Float ids make dict keys and comparisons flaky (`2.0` vs `2`). Dropping NaN-player rows from `pbp_players` up front means Timeout / Start Period / End Period / team-rebound rows can't leak into your evidence later — one filter instead of five special cases. Sorting once here means every downstream loop can assume order.
**Expect:** `pbp.shape == (1011, 30)`. `pbp_players.shape[0] == 1284` (1357 minus 73 NaN-player rows). `rosters.shape == (66, 12)`. `pbp.play_id.dtype` is `int64`.

<details><summary>Hint</summary>

`df[cols] = df[cols].astype(int)` casts several columns at once. `df.sort_values([...]).reset_index(drop=True)` so the index is clean. Return a tuple; call it as `pbp, pbpp, ros = load()`.

</details>
<details><summary>Skeleton</summary>

```python
ID_COLS_PBP  = ["event_id", "play_id", "play_sequence", "period",
                "home_team_id", "away_team_id", "play_team_id"]
ID_COLS_PBPP = ["event_id", "play_id", "play_sequence", "period", "player_id", "team_id"]
ID_COLS_ROS  = ["event_id", "team_id", "player_id"]

def load(data_dir: str = DATA_DIR):
    pbp  = pd.read_excel(f"{data_dir}/pbp.xlsx")
    pbpp = pd.read_excel(f"{data_dir}/pbp-players.xlsx")
    ros  = pd.read_excel(f"{data_dir}/rosters.xlsx")

    # team-event rows (timeouts, period start/end, team rebounds) have no player
    pbpp = pbpp[pbpp.player_id.notna()].copy()

    # ids load as float64 because other columns have NaN; make them real ints
    pbp[ID_COLS_PBP]   = pbp[ID_COLS_PBP].astype(int)
    pbpp[ID_COLS_PBPP] = pbpp[ID_COLS_PBPP].astype(int)
    ros[ID_COLS_ROS]   = ros[ID_COLS_ROS].astype(int)
    # NOTE: leave pbpp.sequence as float — the 20 Starting Lineup rows have NaN there.
    #       1.0 == 1 is True in Python, so comparing to SUB_IN still works.

    pbp  = pbp.sort_values(["event_id", "play_id", "play_sequence"]).reset_index(drop=True)
    pbpp = pbpp.sort_values(["event_id", "play_id", "play_sequence"]).reset_index(drop=True)
    ros  = ros.sort_values(["event_id", "team_id", "player_id"]).reset_index(drop=True)
    return pbp, pbpp, ros
```

`.copy()` after the boolean filter avoids pandas' `SettingWithCopyWarning` on the next line.

</details>

---

### 3.3 Section 3 — lookups [→ R3 — Trap 1 fix]

- [ ] **Do (a):** `player_team_map(rosters) -> dict[(event_id, player_id), team_id]`. One line from `rosters`.
- [ ] **Do (b):** `home_team_map(pbp) -> dict[event_id, home_team_id]`. One line from `pbp` (drop duplicates on `event_id` first).
- [ ] **Do (c):** `game_teams(rosters) -> dict[event_id, set[team_id]]` — the two team ids per game. You'll iterate over these in 3.4.
**Why:** (a) is Trap 1's fix: the single source of truth for who plays for whom. (b) feeds the `is_home` column in Phase 4.2. (c) saves you from hard-coding "two teams" and from deriving teams off `pbp_players` (which is exactly what Trap 1 says not to trust).
**Expect:** `len(team_map) == 66`. `team_map[(1947312, 845564)] == 21` (Booker → Phoenix). `home[1947160] == 2`, `home[1947312] == 21`. `game_teams[1947160] == {2, 9}`.

<details><summary>Hint</summary>

`dict(zip(zip(ros.event_id, ros.player_id), ros.team_id))` or `ros.set_index([...]).team_id.to_dict()`. For (c), `ros.groupby("event_id").team_id.apply(set).to_dict()`.

</details>
<details><summary>Skeleton</summary>

```python
def player_team_map(ros: pd.DataFrame) -> dict[tuple[int, int], int]:
    """(event_id, player_id) -> team_id. Rosters are the only source of truth for this."""
    return ros.set_index(["event_id", "player_id"])["team_id"].to_dict()

def home_team_map(pbp: pd.DataFrame) -> dict[int, int]:
    """event_id -> home_team_id."""
    return pbp.drop_duplicates("event_id").set_index("event_id")["home_team_id"].to_dict()

def game_teams(ros: pd.DataFrame) -> dict[int, set[int]]:
    """event_id -> {team_id, team_id}."""
    return ros.groupby("event_id")["team_id"].apply(set).to_dict()
```

</details>

---

### 3.4 Section 4 — `period_openers()` — **the hard part** [→ R3 — the core requirement]

Signature: `period_openers(pbp_players, team_map, game_teams) -> dict[(event_id, period, team_id), set[player_id]]`. Build it in four sub-steps; run after each.

- [ ] **3.4a — Period 1 from the Starting Lineup rows.** [→ R3]
**Do:** For each game, take `pbp_players` rows where `play_id == STARTING_LINEUP_PLAY_ID`. Group the `player_id`s by team using `team_map` (not `pbpp.team_id`). Store as `result[(event_id, 1, team_id)] = set_of_5`.
**Why:** Ground truth, handed to you. Also becomes the oracle for 3.4d.
**Expect:** 4 keys, each a set of 5.

- [ ] **3.4b — Periods ≥ 2: evidence scan.** [→ R3]
**Do:** For each `(event_id, period)` with `period >= 2`: iterate its `pbp_players` rows **in order** (they're sorted from `load()`). Keep two per-team sets: `subbed_in` and `openers`. For each row, resolve `team = team_map[(event_id, player_id)]`. Then:
  - if it's a Substitution with `sequence == SUB_IN` → add player to `subbed_in[team]`
  - if it's a Substitution with `sequence == SUB_OUT` and player **not in** `subbed_in[team]` → add to `openers[team]` (he left before he arrived, so he must have started)
  - otherwise (any other event) if player **not in** `subbed_in[team]` → add to `openers[team]` (he did something before being brought in, so he must have started)

  Store `result[(event_id, period, team)] = openers[team]`.
**Why:** No subs at period breaks (2.5), so the opening five leaves only two fingerprints: getting subbed out, or appearing in a play. Order matters — a player subbed in at 8:00 who then rebounds at 6:00 must *not* count, hence the `subbed_in` check.
**Expect:** 12 more keys. **Two of them will have 6 players** — Houston P2 and Phoenix P4. That's expected at this sub-step. Print `{k: len(v) for k, v in result.items()}` and confirm you see the two 6s.

- [ ] **3.4c — Apply the exclusion.** [→ R3]
**Do:** In the "otherwise" branch, skip rows where `play_detail == TECHNICAL`. Re-run.
**Why:** Trap 2. (Trap 1 is already handled because you resolved team via `team_map` in 3.4b — if you'd used `pbpp.team_id`, Booker would have landed in Houston's set.)
**Expect:** **All 16 keys have exactly 5.** If any is still 6: you're using `pbpp.team_id` somewhere, or the technical filter isn't reached. If any is 4: you're filtering out a legitimate event type — check you're not excluding all fouls, or all `sequence=3` rows.

- [ ] **3.4d — Self-test on Period 1.** [→ optional — evidence for R9]
**Do:** Run the 3.4b/c logic on period 1 as well (temporarily, or as a separate flag) and compare its answer to 3.4a's Starting Lineup sets. They should be identical for all 4 team-periods.
**Why:** This proves the inference rule recovers ground truth where ground truth exists. It's one paragraph in the walkthrough and it's the strongest evidence you can offer that the Q2–Q4 answers are right. Keep the code — it becomes a test in 4.4.
**Expect:** 4/4 match.

<details><summary>Hint</summary>

Iterate with `for row in group.itertuples(index=False)` — much faster than `iterrows` and gives attribute access (`row.player_id`). `groupby(["event_id", "period"])` yields `((eid, per), frame)` pairs. Use `dict.setdefault(team, set())` or initialise both sets for every team in `game_teams[event_id]` before the loop so a team with zero evidence still gets a key (it'll be an empty set — and your validation in 4.3 will catch it). Sanity-print after each sub-step: `{k: len(v) for k, v in result.items()}`.

Spot-check vs what the data says: game `1947160` P2 BOS opener includes Baynes and Smart; GS includes Thompson and West.

</details>
<details><summary>Skeleton</summary>

```python
def period_openers(pbpp: pd.DataFrame, team_map: dict, teams_by_game: dict) -> dict:
    """(event_id, period, team_id) -> set of 5 player_ids on the floor when the period started."""
    result = {}

    for (eid, per), grp in pbpp.groupby(["event_id", "period"], sort=True):
        teams = teams_by_game[eid]

        # ---- 3.4a: period 1 is given to us ----
        if per == 1:
            starters = grp[grp.play_id == STARTING_LINEUP_PLAY_ID]
            for t in teams:
                result[(eid, 1, t)] = {int(p) for p in starters.player_id
                                       if team_map[(eid, int(p))] == t}
            continue

        # ---- 3.4b: periods 2+ must be inferred ----
        subbed_in = {t: set() for t in teams}
        openers   = {t: set() for t in teams}

        for row in grp.itertuples(index=False):          # grp is already sorted by play_id, play_sequence
            pid = int(row.player_id)
            t   = team_map[(eid, pid)]                    # TRAP 1: never row.team_id

            if row.play_event == "Substitution":
                if row.sequence == SUB_IN:
                    subbed_in[t].add(pid)
                elif row.sequence == SUB_OUT and pid not in subbed_in[t]:
                    openers[t].add(pid)                   # left before arriving -> was a starter
            else:
                if row.play_detail == TECHNICAL:          # TRAP 2 (3.4c): techs can come from the bench
                    continue
                if pid not in subbed_in[t]:
                    openers[t].add(pid)                   # did something before arriving -> was a starter

        for t in teams:
            result[(eid, per, t)] = openers[t]

    return result
```

Run it, then in a cell: `{k: len(v) for k, v in openers.items()}` — 16 keys, all `5`. For 3.4b-before-3.4c, comment out the `TECHNICAL` `continue` and watch two of them become `6`.

For 3.4d, the P1 self-test: temporarily change `if per == 1:` to `if False:` (or add a `use_starting_lineup=True` parameter) and compare the four P1 sets to the Starting Lineup sets.

</details>

**✅ Done when:** 16 keys, every set has exactly 5, and the P1 self-test matches 4/4.

---

## Phase 4 — `on_court.py`: walk → long → validate (≈1.5 hrs) [→ R2, R3]

### 4.1 Section 5 — `walk_plays()` [→ R2, R3]

Signature: `walk_plays(pbp, pbp_players, openers, game_teams) -> dict[(event_id, play_id), dict[team_id, frozenset[player_id]]]`. Build in three sub-steps.

- [ ] **4.1a — The play list.** [→ R2]
**Do:** From `pbp`, take `event_id, play_id, period`, `drop_duplicates()`, sort by `(event_id, play_id)`. This is the list you'll emit one lineup for.
**Why:** `pbp` has 1,011 rows but 993 plays (2.3). Deduping here is what makes "play_id 1 appears once" true.
**Expect:** 993 rows. 489 for game `1947160`, 504 for `1947312`.

- [ ] **4.1b — Index the substitutions by play.** [→ R3]
**Do:** From `pbp_players`, take Substitution rows. Build `subs_by_play: dict[(event_id, play_id), list[(team_id, in_player, out_player)]]`. Resolve `team_id` via `team_map`. Pair the IN and OUT rows of each play (they share `play_id`; `sequence` tells you which is which).
**Why:** In the walk you want O(1) "does this play have a sub?" — not a filter per play.
**Expect:** 104 keys, every list has exactly one `(team, in, out)` tuple (no play has two subs in this data — but don't assume it; a list handles the general case).

- [ ] **4.1c — The walk.** [→ R3]
**Do:** For each game, loop over its plays in order. Keep `on_court: dict[team_id, set[player_id]]`. Whenever `period` differs from the previous play's period (including the very first play), **replace** `on_court` with fresh copies of `openers[(event_id, period, team)]` for each team. If `(event_id, play_id)` is in `subs_by_play`, for each `(team, in, out)`: `on_court[team].remove(out)` then `.add(in)`. Then store `result[(event_id, play_id)] = {team: frozenset(players) for ...}`.
**Why:** Single ordered pass — this is the O(P) core. The period reset is what makes Q2–Q4 work: you don't carry Q1's closers into Q2, you start Q2 from the back-solved openers. Storing a `frozenset` (or `set(...)` copy) per play is mandatory: if you store the live `set`, every play points at the same mutating object and your whole table shows the final lineup.
**Expect:** `len(result) == 993`. Every value has 2 teams × exactly 5 players. **`.remove(out)` should never raise `KeyError`** — if it does, your model has a player leaving who wasn't there. Let it raise during dev (it's your bug detector); print the `play_id` and `play_text` and go look. In the final version catch it, log the play, and re-raise.

Decision to write down for the walkthrough: **a substitution takes effect on its own play row** (you apply the sub, *then* emit). Sub rows never score, so it's analytically inert — but say you chose it.

<details><summary>Hint</summary>

Loop over the play list with `itertuples`. Track `prev_period = None` and compare. Copy openers with `{t: set(openers[(eid, per, t)]) for t in teams}` — `set(...)` makes a copy; assigning the dict value directly does not. For the sub pairing, `groupby(["event_id", "play_id"])` on the sub rows and pick `row.sequence == SUB_IN` / `SUB_OUT` inside each group.

</details>
<details><summary>Skeleton</summary>

```python
def index_subs(pbpp: pd.DataFrame, team_map: dict) -> dict:
    """(event_id, play_id) -> [(team_id, player_in, player_out), ...]"""
    subs = pbpp[pbpp.play_event == "Substitution"]
    out = {}
    for (eid, pid), g in subs.groupby(["event_id", "play_id"]):
        p_in  = int(g.loc[g.sequence == SUB_IN,  "player_id"].iloc[0])
        p_out = int(g.loc[g.sequence == SUB_OUT, "player_id"].iloc[0])
        out.setdefault((eid, pid), []).append((team_map[(eid, p_in)], p_in, p_out))
    return out


def walk_plays(pbp: pd.DataFrame, subs_by_play: dict, openers: dict, teams_by_game: dict) -> dict:
    """(event_id, play_id) -> {team_id: frozenset of 5 player_ids}"""
    plays = (pbp[["event_id", "play_id", "period"]]
             .drop_duplicates()
             .sort_values(["event_id", "play_id"]))

    result = {}
    for eid, gplays in plays.groupby("event_id"):
        teams = teams_by_game[eid]
        on_court, prev_period = None, None

        for row in gplays.itertuples(index=False):
            if row.period != prev_period:                      # new period -> reset to that period's openers
                on_court = {t: set(openers[(eid, row.period, t)]) for t in teams}   # set(...) = COPY
                prev_period = row.period

            for team, p_in, p_out in subs_by_play.get((eid, row.play_id), []):
                on_court[team].remove(p_out)                   # KeyError here = your model is wrong; go look at this play
                on_court[team].add(p_in)

            result[(eid, row.play_id)] = {t: frozenset(s) for t, s in on_court.items()}   # frozenset = snapshot

    return result
```

`set(openers[...])` and `frozenset(s)` are both copies. Drop either one and every play will show the same final lineup.

</details>

---

### 4.2 Section 6 — `to_long()` [→ R2, R3, T1 — the table design]

- [ ] **Do:** `to_long(on_court, plays, home_map) -> DataFrame` with columns `event_id, play_id, player_id, team_id, period, is_home`. Loop over `on_court`; for each play, for each team, for each player, append one row. `period` comes from a `{(event_id, play_id): period}` lookup built off the play list; `is_home = int(team_id == home_map[event_id])`. Build the frame from a list of tuples once at the end — not `df.append` in a loop.
**Why:** This is the table grain (10 rows per play). Denormalised `team_id / period / is_home` are deliberate: the "points while on court" query needs one join to `pbp` instead of two.
**Expect:** `df.shape == (9930, 6)`. `df.groupby(["event_id", "play_id"]).size().eq(10).all()` is `True`. `df.is_home.mean() == 0.5`.

<details><summary>Hint</summary>

Accumulate `rows.append((eid, pid, player, team, period, is_home))`, then `pd.DataFrame(rows, columns=[...])`. Sort by `(event_id, play_id, team_id, player_id)` so the output is deterministic — makes diffs and the SQL dump stable between runs.

</details>
<details><summary>Skeleton</summary>

```python
OUT_COLS = ["event_id", "play_id", "player_id", "team_id", "period", "is_home"]

def to_long(on_court: dict, pbp: pd.DataFrame, home_map: dict) -> pd.DataFrame:
    period_of = (pbp[["event_id", "play_id", "period"]].drop_duplicates()
                 .set_index(["event_id", "play_id"])["period"].to_dict())
    rows = []
    for (eid, pid), teams in on_court.items():
        for t, players in teams.items():
            for p in players:
                rows.append((eid, pid, p, t, period_of[(eid, pid)], int(t == home_map[eid])))
    return (pd.DataFrame(rows, columns=OUT_COLS)
            .sort_values(["event_id", "play_id", "team_id", "player_id"])
            .reset_index(drop=True))
```

</details>

---

### 4.3 Section 7 — `validate()` [→ R2, R3 — proven in code]

- [ ] **Do:** `validate(df, pbp, rosters) -> None`. Raise `AssertionError` with a **specific message** (which game, which play, what count) on the first failure. Five checks:
  1. **Coverage** — per game, `set(pbp.play_id) == set(df.play_id)`. Message: which play_ids are missing / extra.
  2. **Ten per play** — every `(event_id, play_id)` has exactly 10 rows. Message: the offending play_ids and their counts.
  3. **Five per team per play** — every `(event_id, play_id, team_id)` has exactly 5.
  4. **On the roster** — every `(event_id, player_id)` in `df` exists in `rosters`.
  5. **No duplicates** — `(event_id, play_id, player_id)` is unique.
  On success, print one line: `validate: 5/5 checks passed, 9930 rows, 993 plays, 2 games`.
**Why:** These are the prompt's requirements ("each play_id represented", "10 players") turned into code. Also your safety net when you refactor.
**Expect:** Passes. Then **break it on purpose** — `df.drop(df.index[0])` — and confirm it fails with a readable message. Restore.

<details><summary>Hint</summary>

`groupby([...]).size()` then `.ne(10)` / `.ne(5)` and `.any()`; index the failures out for the message. Set difference for coverage: `missing = pbp_ids - df_ids`. For roster membership, build a set of `(event_id, player_id)` tuples from `rosters` and check with `MultiIndex.isin` or a merge with `indicator=True`.

</details>
<details><summary>Skeleton</summary>

```python
def validate(df: pd.DataFrame, pbp: pd.DataFrame, ros: pd.DataFrame) -> None:
    # 1. coverage: every play_id in pbp appears in df, per game
    for eid, g in pbp.groupby("event_id"):
        missing = set(g.play_id) - set(df.loc[df.event_id == eid, "play_id"])
        assert not missing, f"game {eid}: {len(missing)} play_ids missing, e.g. {sorted(missing)[:5]}"

    # 2. exactly 10 per play
    per_play = df.groupby(["event_id", "play_id"]).size()
    bad = per_play[per_play != 10]
    assert bad.empty, f"{len(bad)} plays without 10 players:\n{bad.head()}"

    # 3. exactly 5 per team per play
    per_team = df.groupby(["event_id", "play_id", "team_id"]).size()
    bad = per_team[per_team != 5]
    assert bad.empty, f"{len(bad)} team-plays without 5 players:\n{bad.head()}"

    # 4. everyone is on that game's roster
    on_roster = df.merge(ros[["event_id", "player_id"]], how="left", indicator=True)
    bad = on_roster[on_roster._merge == "left_only"]
    assert bad.empty, f"{len(bad)} rows with players not on the roster:\n{bad.head()}"

    # 5. no duplicate (event, play, player)
    dupes = df.duplicated(["event_id", "play_id", "player_id"]).sum()
    assert dupes == 0, f"{dupes} duplicate rows"

    print(f"validate: 5/5 checks passed — {len(df)} rows, {len(per_play)} plays, {df.event_id.nunique()} games")
```

</details>

---

### 4.4 `test_on_court.py` (≈30 min) [→ optional — credibility]

- [ ] **Do:** Create `test_on_court.py` next to the script. `from on_court import load, player_team_map, ..., period_openers, walk_plays, to_long, validate`. A module-level fixture (`@pytest.fixture(scope="module")`) that calls `load()` once. Then 5–6 tests:
  - `test_team_map_puts_booker_on_phoenix` — `team_map[(1947312, 845564)] == 21`
  - `test_openers_all_five` — 16 keys, every `len == 5`
  - `test_openers_recover_period_one_starters` — the 3.4d self-test
  - `test_walk_covers_every_play` — 993 keys, each 2 teams × 5
  - `test_long_shape` — 9930 rows, 10 per play
  - `test_walk_applies_sub` — a **hand-built** tiny frame: 3 plays, one sub, known answer. Tests the loop logic without the real data.
**Why:** The prompt doesn't demand tests; a small suite that runs in 3 s is cheap credibility, and the hand-built case is the only one that isolates the sub logic.
**Expect:** `pytest -q` → all green, under 10 s.

<details><summary>Hint</summary>

For the hand-built case, build `pbp` and `pbpp` DataFrames with the minimum columns your functions touch, plus a tiny `openers` dict — you don't need all 30 columns. If `load()` is slow to import, the module-scoped fixture means it runs once per `pytest` invocation.

</details>

**✅ Done when:** `validate()` passes on the real frame, fails loudly on a broken one, and `pytest -q` is green.

---

## Phase 5 — MySQL write + dump + your own analysis (≈1.5 hrs) [→ R4–R8, T1]

### 5.1 Section 8 — `write_mysql()` [→ R4, R5, R7]

- [ ] **5.1a — Connection.** [→ R7] **Do:** `get_conn()` returns `mysql.connector.connect(host=, port=, user=, password=, database=)` with every value from `os.environ[...]` (the names in `.env.example`). No defaults for password. Cast port to `int`.
**Why:** "Remove any private connection parameters" — there are none in the code to remove.

- [ ] **5.1b — DDL.** [→ R4] **Do:** Module-level `DDL = """CREATE TABLE IF NOT EXISTS pbp_players_on_court (...)"""` — exactly the schema in `CLAUDE.md`: 6 data columns + `updated_at`, composite PK `(event_id, play_id, player_id)`, two secondary indexes.
**Why:** `IF NOT EXISTS` makes first run and every later run the same code path.

- [ ] **5.1c — The write.** [→ R4, R5] **Do:** `write_mysql(df, conn)`. Open a cursor, execute the DDL. Then **per game**: `DELETE FROM pbp_players_on_court WHERE event_id = %s`, then `executemany(INSERT ... VALUES (%s,%s,%s,%s,%s,%s), rows)` where `rows` is a list of tuples of **plain Python ints**. One `conn.commit()` after all games. Wrap in `try / except: conn.rollback(); raise`. Return the row count written.
**Why:** Delete-then-insert per game makes a rerun produce *exactly* the source — no orphans if a play was corrected away upstream (an upsert would leave them). Single commit = atomic across games. This is the "run it a second time, it updates" requirement, and the rollback is what makes it safe.
**Expect:** Returns 4890 for one game, 9930 for both.

**Gotcha you will hit:** mysql-connector rejects numpy integer types — `TypeError: Failed processing format-parameters; Python 'int64' cannot be converted to a MySQL type`. Convert every value with `int()` when building tuples. `df.astype(object)` before `.itertuples()` is not enough on its own — cast explicitly.

<details><summary>Hint</summary>

`rows = [tuple(int(v) for v in r) for r in df[COLS].itertuples(index=False, name=None)]`. `executemany` sends ~5k rows in one round trip on this connector. Use `with conn.cursor() as cur:` if your connector version supports it; otherwise `cur.close()` in `finally`.

</details>
<details><summary>Skeleton</summary>

```python
DDL = """
CREATE TABLE IF NOT EXISTS pbp_players_on_court (
  event_id   INT        NOT NULL,
  play_id    INT        NOT NULL,
  player_id  INT        NOT NULL,
  team_id    INT        NOT NULL,
  period     TINYINT    NOT NULL,
  is_home    TINYINT(1) NOT NULL,
  updated_at TIMESTAMP  NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (event_id, play_id, player_id),
  KEY ix_player (event_id, player_id),
  KEY ix_team   (event_id, team_id, play_id)
)
"""
INSERT_SQL = """
INSERT INTO pbp_players_on_court (event_id, play_id, player_id, team_id, period, is_home)
VALUES (%s, %s, %s, %s, %s, %s)
"""

def get_conn():
    return mysql.connector.connect(
        host=os.environ["MYSQL_HOST"],
        port=int(os.environ["MYSQL_PORT"]),
        user=os.environ["MYSQL_USER"],
        password=os.environ["MYSQL_PASSWORD"],
        database=os.environ["MYSQL_DATABASE"],
    )

def write_mysql(df: pd.DataFrame, conn) -> int:
    cur = conn.cursor()
    try:
        cur.execute(DDL)
        written = 0
        for eid in sorted(df.event_id.unique()):
            g = df[df.event_id == eid]
            cur.execute("DELETE FROM pbp_players_on_court WHERE event_id = %s", (int(eid),))
            # mysql-connector rejects numpy ints -> convert every value with int()
            rows = [tuple(int(v) for v in r) for r in g[OUT_COLS].itertuples(index=False, name=None)]
            cur.executemany(INSERT_SQL, rows)
            written += len(rows)
        conn.commit()                                 # one commit: all games or none
        return written
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
```

</details>

---

### 5.2 Section 9 — `main()` + argparse [→ R6, R7]

- [ ] **Do:** `argparse` with `--game` (required; `"all"` or an integer event_id), `--validate` (flag), `--no-db` (flag — build and validate, skip the write; handy in dev). `main()`: `load()`; if `--game` is an id, filter all three frames to it and exit with a clear message if the id isn't in `pbp`; build lookups → `period_openers` → `walk_plays` → `to_long`; `validate` if asked; `write_mysql` unless `--no-db`; print a one-line summary. Guard with `if __name__ == "__main__": sys.exit(main())`.
**Why:** The prompt's "run for one game or all" requirement. `--no-db` lets you iterate without Docker running.

- [ ] **Run the sequence and record what you see** (you'll paste it into the walkthrough):
  1. `python on_court.py --game 1947160` → then in the mysql shell: `SELECT COUNT(*) FROM pbp_players_on_court;` → **4890**
  2. `python on_court.py --game all` → count → **9930**
  3. `python on_court.py --game all` **again** → count still **9930**, not 19860. Idempotency proof.
  4. `python on_court.py --game 999` → clean one-line error, exit code 1, no stack trace.
  5. `python on_court.py --game all --validate` → `validate: 5/5 checks passed ...`

<details><summary>Hint</summary>

`parser.add_argument("--game", required=True)` then `if args.game != "all": eid = int(args.game)`. Filter with `pbp[pbp.event_id == eid]` etc. — and don't forget to filter `rosters` too or `game_teams` will still have both games. `return 0` / `return 1` from `main()` and let `sys.exit` carry it.

</details>
<details><summary>Skeleton</summary>

```python
def main() -> int:
    ap = argparse.ArgumentParser(description="Derive the 10 players on court for every play.")
    ap.add_argument("--game", required=True, help='an event_id, or "all"')
    ap.add_argument("--validate", action="store_true", help="run integrity checks before writing")
    ap.add_argument("--no-db", action="store_true", help="build + validate only; skip MySQL")
    args = ap.parse_args()

    pbp, pbpp, ros = load()

    if args.game != "all":
        eid = int(args.game)
        if eid not in set(pbp.event_id):
            print(f"error: event_id {eid} not found in pbp", file=sys.stderr)
            return 1
        pbp, pbpp, ros = (pbp[pbp.event_id == eid], pbpp[pbpp.event_id == eid], ros[ros.event_id == eid])

    team_map = player_team_map(ros)
    home_map = home_team_map(pbp)
    teams    = game_teams(ros)
    openers  = period_openers(pbpp, team_map, teams)
    subs     = index_subs(pbpp, team_map)
    on_court = walk_plays(pbp, subs, openers, teams)
    df       = to_long(on_court, pbp, home_map)

    if args.validate:
        validate(df, pbp, ros)

    if not args.no_db:
        n = write_mysql(df, get_conn())
        print(f"wrote {n} rows for {df.event_id.nunique()} game(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

</details>

---

### 5.3 `sql/validation.sql` — the "do your own calculations" tip [→ T1 — their tip; optional but recommended]

- [ ] **Do (a):** Get `pbp` into MySQL so you can join to it. Simplest: add a `--load-source` flag to `on_court.py` that writes `pbp`, `pbp_players`, `rosters` into same-named tables with the same executemany pattern from 5.1 (`CREATE TABLE IF NOT EXISTS`, then `DELETE`/`INSERT` per game). Only the columns you need: for `pbp` at least `event_id, play_id, play_sequence, period, play_team_id, points_scored, play_event, play_text`. Say in the walkthrough it's a dev convenience, not part of the deliverable table.
- [ ] **Do (b):** Write `sql/validation.sql`. Query 1: **team points scored while each player was on court** — join `pbp_players_on_court oc` to `pbp p` on `(event_id, play_id)`, sum `points_scored` where `p.play_team_id = oc.team_id` as `pts_for`, where `<>` as `pts_against`, `COUNT(DISTINCT p.play_id)` as `plays_on_court`, grouped by `event_id, team_id, player_id`. Query 2: **the reconciliation** — per `(event_id, team_id)`, `SUM(pts_for)` from query 1 should equal `5 ×` the team's total `SUM(points_scored)` from `pbp` (five players share every point). Put both side by side with the difference.
**Why:** The prompt literally suggests this. Query 2 is a proof: if lineups were wrong (a 4 or 6 somewhere, or the wrong player), the 5× identity breaks. Paste the numbers into the walkthrough.
**Expect:** Query 2 difference = 0 for all 4 team-games. If not zero, a lineup has the wrong count somewhere — `validate()` should already have caught it; if `validate` passes and this doesn't, your `play_team_id` join or `points_scored` NaN handling is off.

<details><summary>Hint</summary>

`SUM(CASE WHEN p.play_team_id = oc.team_id THEN p.points_scored ELSE 0 END)`. `points_scored` has NaN in the source — write it as `NULL` and `SUM` ignores it, or `fillna(0)` before loading. Run the file with SQLTools (`Ctrl+E Ctrl+E`) or `docker exec -it swish-mysql mysql -u swish -p swish` and paste.

</details>

---

### 5.4 The dump deliverable [→ R8]

- [ ] **Do:** Dump inside the container, then copy the file out — this sidesteps PowerShell's redirect-encoding problems entirely:

```bash
docker exec swish-mysql sh -c "mysqldump -u root -p\$MYSQL_ROOT_PASSWORD swish pbp_players_on_court --result-file=/tmp/dump.sql"
```
```bash
docker cp swish-mysql:/tmp/dump.sql sql/pbp_players_on_court.sql
```

- [ ] Open `sql/pbp_players_on_court.sql`. It should have one `CREATE TABLE` and a handful of large `INSERT INTO ... VALUES (...),(...)` statements. Roughly 400–600 KB.
- [ ] **Prove it restores.** In the mysql shell `CREATE DATABASE swish_check;`, then:

```bash
docker exec swish-mysql sh -c "mysql -u root -p\$MYSQL_ROOT_PASSWORD swish_check < /tmp/dump.sql"
```

then `SELECT COUNT(*) FROM swish_check.pbp_players_on_court;` → **9930**. `DROP DATABASE swish_check;` after.
**Why:** A dump that doesn't restore is worth nothing to the reviewer. Thirty seconds to verify.

**✅ Done when:** rerun is idempotent (9930 twice), dump restores to 9930, reconciliation difference is 0.

---

## Phase 6 — Part 1 writeup: `docs/walkthrough.md` (≈1.5 hrs) [→ R9]

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

## Phase 7 — Part 2: diagram + `docs/system-design.md` (≈2–3 hrs) [→ R10, R11]

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

## Phase 8 — Package & submit (≈45 min) [→ R7, R8]

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
