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
data and have to be inferred (Phase 3.3). Everything else is plumbing.

**What's optional:** all of Phase 2 (understanding, not code), 3.4, 4.5, and the tests in 5.3.
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

## Phase 3 — `on_court.ipynb`: load → openers (≈1 hr) [→ R1, R3]

You're developing in **`on_court.ipynb`**. Rules for this and the next two phases:

- **One idea per cell.** A *define* cell holds one function. A *run* cell calls
  it and ends with a bare expression so the notebook renders the result as a
  table. Never define and run in the same cell.
- **Every run cell has a "You should see."** If you don't see it, the **If not**
  fold says what to check. Don't move on until it matches.
- **Frames in, frames out.** No dict lookups, no row loops in this phase.
- **Count cells end in `.reset_index(name="…")`** so the output is a normal
  3-column table instead of a Series with tuple index (that's what the
  `(np.int64(…), np.int64(…))` / `# 0` rendering was).
- **Style:** yours. Black, type hints, one-line docstring, name the result
  before you `return` it.
- **The deliverable is still `on_court.py`.** At the end of Phase 5 you export
  the notebook and add `main()`.

### What Phase 3 produces

One DataFrame, **`openers`** — who was on the floor when each period started:

```
event_id  period  team_id  player_id
 1947160       1        2     280587
 ...                                    80 rows = 2 games × 4 periods × 2 teams × 5 players
```

Two functions build it:

```
pbpp ──► attach_roster_team() ──► pbpp with the ROSTER's team_id     (Trap 1, fixed once)
                │
                └──► period_openers() ──► openers                    (one rule, all periods)
```

**The rule:** use the feed's explicit lineup where it exists; infer only where it
doesn't. Q1 comes straight from the Starting Lineup rows at `play_id 1`. For
Q2+, drop technical fouls and look at the **first row** each player appears in:
if that row is him being subbed **in**, he started on the bench; anything else —
a shot, a rebound, a foul, being subbed **out** — means he was already on the floor.

(The inference rule also reproduces Q1 exactly when run on Q1 — that's your
Phase 3.4 self-test — but trusting the explicit rows is the safer default.)

### Clean-up first

- [ ] Delete `player_team_map()`, `home_team_map()`, `game_teams()`, and any `starting_five()` / `inferred_openers()` you've typed, plus their run cells. Two functions replace all of them.

---

### 3.1 — `load()` [→ R1, T2] — **done**

Matches. `pbpp.sequence` stays float on purpose (the 20 Starting Lineup rows are `NaN` there); leave it out of `ID_COLS_PBPP`. `1.0 == SUB_IN` is `True`.

- [ ] **Run cell:**

```python
pbp, pbpp, ros = load(DATA_DIR)
pbp.shape, pbpp.shape, ros.shape
```

**You should see:** `((1011, 30), (1284, 38), (66, 12))`.

---

### 3.2 — `attach_roster_team()` [→ R3 — Trap 1 fix]

- [ ] **Do:** Join the roster's `team_id` onto `pbpp` by `(event_id, player_id)` and **overwrite** `pbpp.team_id` with it. Return the frame.
**Why:** `pbpp.team_id` is wrong on one row (Booker, play 149, tagged HOU). Rosters are the truth. Fix it once here and everything downstream can trust `pbpp.team_id`.

<details><summary>Skeleton</summary>

```python
def attach_roster_team(pbpp: pd.DataFrame, ros: pd.DataFrame) -> pd.DataFrame:
    """Replace pbpp.team_id with the roster's team_id (pbpp's is wrong on 1 row)."""

    roster_team = ros.set_index(["event_id", "player_id"])["team_id"].rename("roster_team_id")
    out = pbpp.join(roster_team, on=["event_id", "player_id"])
    out["team_id"] = out.pop("roster_team_id").astype(int)
    return out
```

`join(..., on=[...])` lines a 2-level-indexed Series up against two columns. `pop` pulls the joined column out and deletes it in one move.

</details>

- [ ] **Run cell:**

```python
pbpp = attach_roster_team(pbpp, ros)
print("unmatched:", pbpp.team_id.isna().sum())
pbpp.loc[pbpp.play_id == 149, ["player_id", "last_name", "team_abbr", "team_id"]]
```

**You should see:** `unmatched: 0`, and Booker's row with `team_abbr = Hou` but `team_id = 21`. That's the bad row, corrected.

<details><summary>If not</summary>

- `KeyError` inside the join → `ros` ids still float; `load()` should have cast them.
- `unmatched > 0` → a `pbpp` player isn't on any roster: `pbpp[pbpp.team_id.isna()][["player_id","last_name"]]`. (In this data: nobody.)
- Booker still `team_id = 10` → you didn't reassign. `pbpp = attach_roster_team(pbpp, ros)`.

</details>

---

### 3.3 — `period_openers()` [→ R3 — the core requirement]

- [ ] **Do (a) — Q1, given.** `starters` = `pbpp` rows where `play_id == STARTING_LINEUP_PLAY_ID`, the 4 opener columns. 20 rows.
- [ ] **Do (b) — Q2+, inferred.** `evidence` = `pbpp` rows with `period >= 2` and `play_detail != TECHNICAL`. `first_row` = `evidence.drop_duplicates(subset=OPENER_COLS, keep="first")` — `load()` sorted by play order, so "first" = earliest. `checked_in` = that row is a `Substitution` with `sequence == SUB_IN`. `inferred` = rows where it isn't.
- [ ] **Do (c) — concat** `starters` and `inferred`. That's `openers`.
**Why:** `play_id` increases through the game, so "first row in the period" is "first thing he did." Deciding on that one row is the entire inference. Q1 doesn't need it because the feed hands you the answer.

<details><summary>Skeleton</summary>

```python
OPENER_COLS = ["event_id", "period", "team_id", "player_id"]


def period_openers(pbpp: pd.DataFrame) -> pd.DataFrame:
    """Q1 from the Starting Lineup rows; Q2+ inferred from each player's first appearance."""

    starters = pbpp.loc[pbpp.play_id == STARTING_LINEUP_PLAY_ID, OPENER_COLS]

    evidence = pbpp[(pbpp.period >= 2) & (pbpp.play_detail != TECHNICAL)]
    first_row = evidence.drop_duplicates(subset=OPENER_COLS, keep="first")
    checked_in = (first_row.play_event == "Substitution") & (first_row.sequence == SUB_IN)
    inferred = first_row.loc[~checked_in, OPENER_COLS]

    openers = pd.concat([starters, inferred], ignore_index=True)
    return openers
```

Two other shapes of the same inference (explicit first-seen/first-in columns; a per-group scan) are in `docs/phase3-options.md`.

</details>

- [ ] **Run cell 1 — look before you trust.** Build `first_row` inline and inspect one team-period:

```python
evidence = pbpp[(pbpp.period >= 2) & (pbpp.play_detail != TECHNICAL)]
first_row = evidence.drop_duplicates(subset=OPENER_COLS, keep="first")
bos_q2 = first_row[(first_row.event_id == 1947160) & (first_row.period == 2) & (first_row.team_id == 2)]
bos_q2[["player_id", "last_name", "play_id", "play_event", "sequence", "play_text"]]
```

**You should see:** ~8 rows. Baynes — defensive rebound at play 118 → opener. Smart — missed shot at 119 → opener. Morris — "Substitution: Marcus Morris in for Daniel Theis" at 129, `sequence 1.0` → bench. Theis — same play 129, `sequence 2.0` (out) → opener.

- [ ] **Run cell 2 — the counts:**

```python
openers = period_openers(pbpp)
counts = openers.groupby(["event_id", "period", "team_id"]).size().reset_index(name="players")
print("groups:", len(counts), "| all 5:", (counts.players == 5).all(), "| rows:", len(openers))
counts
```

**You should see:** `groups: 16 | all 5: True | rows: 80` and a clean 16-row, 4-column table. **`openers` is Phase 3's output.**

- [ ] **Run cell 3 — human-readable view** (for you and for the walkthrough; not part of the script):

```python
def openers_wide(openers: pd.DataFrame, ros: pd.DataFrame) -> pd.DataFrame:
    """One row per (game, team); one column per period listing the five who opened it."""

    named = openers.merge(ros[["event_id", "player_id", "name"]], on=["event_id", "player_id"])
    named["label"] = named.name + " (" + named.player_id.astype(str) + ")"
    wide = (
        named.sort_values("name")
        .groupby(["event_id", "team_id", "period"])["label"]
        .agg(", ".join)
        .unstack("period")
        .rename(columns=lambda p: f"Q{p}")
        .rename_axis(columns=None)
        .reset_index()
    )
    return wide


pd.set_option("display.max_colwidth", None)
openers_wide(openers, ros)
```

**You should see:** 4 rows × `event_id, team_id, Q1, Q2, Q3, Q4`. Every Q3 equals its Q1 (starters return after halftime). HOU Q2 has no Booker; PHO Q4 has no Warren.

<details><summary>If not</summary>

- **A `6`** → a trap leaked. Houston P2 → Trap 1: `attach_roster_team` didn't run or you didn't reassign `pbpp`. Phoenix P4 → Trap 2: `play_detail != TECHNICAL` is missing.
- **A `4`** → you're excluding real evidence. Only technicals go; every other event and every `sequence` value counts.
- **Q1 wrong** → `starters` filter is off; should be exactly 20 rows before the concat.
- **Q2+ wrong order / wrong "first"** → `pbpp` isn't sorted. `load()` must `sort_values(["event_id", "play_id", "play_sequence"])`.
- To see *who* is in a suspicious group: `openers.merge(ros[["event_id", "player_id", "name"]])`, filter.

</details>

---

### 3.4 — Self-test on period 1 [→ optional — evidence for R9]

- [ ] **Do:** Run the *inference half* on Q1 and compare it to the *given half*. Easiest: temporarily change `period >= 2` to `period >= 1` (or add a `min_period=2` parameter), take the inferred rows where `period == 1`, and `.equals()` them against `starters`. Sort both by `OPENER_COLS`, `reset_index(drop=True)` first.
**Why:** In Q1 the feed tells you the answer. If the inference reproduces it, that's direct evidence the Q2–Q4 answers (where there's no key) are right. Say in the walkthrough that the Starting Lineup rows themselves count as "first appearance" here, so also run it with `play_id != 1` excluded from the evidence — it still matches, and that's the honest version of the test.

**You should see:** `True`, both ways.

**✅ Done when:** `openers` has 80 rows in 16 groups of 5.

---

## Phase 4 — `on_court.ipynb`: subs → walk → validate (≈1.5 hrs) [→ R2, R3]

### 4.1 — `sub_events()` [→ R3]

- [ ] **Do:** Substitution rows of `pbpp`, pivoted so each sub is **one row**: `event_id, play_id, period, team_id, player_in, player_out`. Index the pivot on `(event_id, play_id, period, team_id)`, columns from `sequence`, values `player_id`. Rename `1 → player_in`, `2 → player_out`.
**Why:** The walk wants "for this play: which team, who in, who out" as a single row. `period` is in there so 4.2 can filter subs to one team-period without joining back to `pbp`.

<details><summary>Skeleton</summary>

```python
def sub_events(pbpp: pd.DataFrame) -> pd.DataFrame:
    """One row per substitution: event_id, play_id, period, team_id, player_in, player_out."""

    subs = pbpp[pbpp.play_event == "Substitution"]
    pivoted = (
        subs.pivot_table(
            index=["event_id", "play_id", "period", "team_id"],
            columns="sequence",
            values="player_id",
            aggfunc="first",
        )
        .rename(columns={SUB_IN: "player_in", SUB_OUT: "player_out"})
        .astype(int)
        .reset_index()
    )
    pivoted.columns.name = None
    return pivoted[["event_id", "play_id", "period", "team_id", "player_in", "player_out"]]
```

Pivot column labels come out as `1.0`/`2.0` (sequence is float); `rename` with the int constants still matches because `1 == 1.0`. `columns.name = None` clears the stray "sequence" label the pivot leaves behind.

</details>

- [ ] **Run cell:**

```python
subs = sub_events(pbpp)
print(subs.shape)
subs.head()
```

**You should see:** `(104, 6)`. First row: game `1947160`, play `41`, period `1`, team `2`, `player_in = 697132` (Smart), `player_out = 937647` (Tatum).

<details><summary>If not</summary>

- Rows ≠ 104 → `team_id` in the index split a sub in two, meaning the IN and OUT rows have different `team_id`s. `attach_roster_team` didn't run.
- `ValueError` on `astype(int)` → a NaN in `player_in`/`player_out` (a sub with one row). `subs.groupby(["event_id","play_id"]).size().value_counts()` should be `{2: 104}`.
- `AttributeError: 'DataFrame' object has no attribute 'period'` later in 4.2 → `period` isn't in the pivot index.

</details>

---

### 4.2 — `add_is_home()` [→ T1 — table design]

- [ ] **Do:** Small helper the walk calls at the end. Take the long frame (5 columns, no `is_home` yet) and `pbp`. Merge `pbp[["event_id", "home_team_id"]].drop_duplicates()` on `event_id`; `is_home = (team_id == home_team_id).astype(int)`. Select `OUT_COLS`, sort, reset index.
**Why:** Keeps `is_home` a frame operation (no `home_team_map` dict), and keeps `walk_plays` about one thing — the lineup replay. Define it **before** `walk_plays` or you'll get `NameError`.

<details><summary>Skeleton</summary>

```python
OUT_COLS = ["event_id", "play_id", "player_id", "team_id", "period", "is_home"]


def add_is_home(long: pd.DataFrame, pbp: pd.DataFrame) -> pd.DataFrame:
    """Attach is_home by comparing team_id to the game's home_team_id."""

    home = pbp[["event_id", "home_team_id"]].drop_duplicates()
    out = long.merge(home, on="event_id")
    out["is_home"] = (out.team_id == out.home_team_id).astype(int)
    result = out[OUT_COLS].sort_values(OUT_COLS[:4]).reset_index(drop=True)
    return result
```

</details>

No run cell of its own — it's exercised by 4.3.

---

### 4.3 — `walk_plays()` — produces the final table [→ R2, R3, T1]

The one loop in the project. Each team's five is independent of the other team's, so replay **one team's period at a time**: start from its five, apply its subs in order, write down who's on the floor at every play. State is a single `set`.

- [ ] **Do (a) — the play list.** `pbp[["event_id", "play_id", "period"]].drop_duplicates()`, sorted by `(event_id, play_id)`.
**Expect:** 993 rows (`pbp` has 1,011 because `play_id 1` is 10 rows).

- [ ] **Do (b) — the loop.** `for (eid, per, team), five in openers.groupby([...])` — `openers` hands you one five at a time. `on_court = set(five.player_id)`. Filter `subs` to that game/period/team and `set_index("play_id")`; filter `plays` to that game/period. Walk the plays: if the play is in `team_subs.index`, `remove(player_out)` then `add(player_in)`. Then `rows.extend(...)` — 5 tuples `(event_id, play_id, player_id, team_id, period)`.
- [ ] **Do (c) — the frame.** `pd.DataFrame(rows, columns=OUT_COLS[:-1])` then `add_is_home(long, pbp)`.
**Why:** Looping per team-period means the period reset is the top of the loop (no `prev_period` tracking), there's one set instead of a dict of sets, and no lookups to build — three boolean filters do it. Iterating the play list 16 times costs microseconds.

**Write this down for the walkthrough:** a sub takes effect **on its own play row** (apply, then record). Sub rows never score, so it's analytically inert — but say you chose it. Three other shapes of this function (per game, per period, a no-loop stints join) are in `docs/phase4-options.md`.

<details><summary>Skeleton</summary>

```python
def walk_plays(pbp: pd.DataFrame, openers: pd.DataFrame, subs: pd.DataFrame) -> pd.DataFrame:
    """One row per (play, on-court player): each team's period replayed from its five."""

    plays = pbp[["event_id", "play_id", "period"]].drop_duplicates().sort_values(["event_id", "play_id"])

    rows = []
    for (eid, per, team), five in openers.groupby(["event_id", "period", "team_id"]):
        on_court = set(five.player_id)
        team_subs = subs[(subs.event_id == eid) & (subs.period == per) & (subs.team_id == team)].set_index("play_id")
        period_plays = plays[(plays.event_id == eid) & (plays.period == per)]

        for play in period_plays.itertuples(index=False):
            if play.play_id in team_subs.index:
                on_court.remove(team_subs.at[play.play_id, "player_out"])
                on_court.add(team_subs.at[play.play_id, "player_in"])

            rows.extend((eid, play.play_id, p, team, per) for p in on_court)

    long = pd.DataFrame(rows, columns=OUT_COLS[:-1])
    return add_is_home(long, pbp)
```

`team_subs.at[...]` assumes one sub per team per play — true in this data. If a feed ever had two, `.loc[play.play_id]` returns a frame and you'd loop it.

</details>

- [ ] **Run cell:**

```python
on_court = walk_plays(pbp, openers, subs)
print(on_court.shape, "| 10 per play:", (on_court.groupby(["event_id", "play_id"]).size() == 10).all())
on_court[(on_court.event_id == 1947160) & on_court.play_id.between(40, 42)].merge(ros[["event_id", "player_id", "name"]])
```

**You should see:** `(9930, 6) | 10 per play: True`, then 30 rows for plays 40–42 in which Jayson Tatum is on court at play 40 and Marcus Smart replaces him from play 41 onward.

<details><summary>If not</summary>

- **`NameError: add_is_home`** → define it first (4.2).
- **`AttributeError: ... 'period'`** on `subs` → 4.1's pivot index needs `period`.
- **`KeyError` at `.remove(...)`** → the walk thinks someone left who wasn't on. Print `eid, per, team, play.play_id` just before the `remove`, look that play up in `pbpp`. Almost always: that team-period's five is wrong (back to 3.3's counts).
- **Rows < 9930** → a team-period missing from `openers`; there should be 16 groups.
- **Rows > 9930 or 15 per play** → `team_subs` matched the other team's sub. Check the `team_id` filter.

</details>

---

### 4.4 — `validate()` [→ R2, R3 — proven in code]

- [ ] **Do:** One function, five `assert`s, each with a message naming the offender; print one summary line on success.
  1. per game, `set(pbp.play_id) == set(on_court.play_id)`
  2. every `(event_id, play_id)` has 10 rows
  3. every `(event_id, play_id, team_id)` has 5 rows
  4. every `(event_id, player_id)` in the output exists in `ros`
  5. `(event_id, play_id, player_id)` has no duplicates
**Why:** R2 and R3 as executable checks, and your regression net when you refactor.

<details><summary>Skeleton</summary>

```python
def validate(on_court: pd.DataFrame, pbp: pd.DataFrame, ros: pd.DataFrame) -> None:
    """Raise AssertionError on the first broken invariant."""

    for eid, g in pbp.groupby("event_id"):
        missing = set(g.play_id) - set(on_court.loc[on_court.event_id == eid, "play_id"])
        assert not missing, f"game {eid}: {len(missing)} play_ids missing, e.g. {sorted(missing)[:5]}"

    per_play = on_court.groupby(["event_id", "play_id"]).size()
    assert (per_play == 10).all(), f"plays without 10 players:\n{per_play[per_play != 10].head()}"

    per_team = on_court.groupby(["event_id", "play_id", "team_id"]).size()
    assert (per_team == 5).all(), f"team-plays without 5 players:\n{per_team[per_team != 5].head()}"

    on_roster = on_court.merge(ros[["event_id", "player_id"]], how="left", indicator=True)
    assert (on_roster._merge == "both").all(), f"players not on roster:\n{on_roster[on_roster._merge != 'both'].head()}"

    dupes = on_court.duplicated(["event_id", "play_id", "player_id"]).sum()
    assert dupes == 0, f"{dupes} duplicate (event, play, player) rows"

    print(f"validate: 5/5 passed — {len(on_court)} rows, {len(per_play)} plays, {on_court.event_id.nunique()} games")
```

</details>

- [ ] **Run cell:** `validate(on_court, pbp, ros)` → the summary line.
- [ ] **Break it on purpose:** `validate(on_court.drop(index=0), pbp, ros)` → `AssertionError` from check 2 naming the play. That's what a reviewer sees if the data ever goes bad.

---

### 4.5 — `test_on_court.py` [→ optional — credibility]

Defer until the functions live in `on_court.py` (Phase 5.3).

**✅ Done when:** `validate(on_court, pbp, ros)` prints `5/5 passed — 9930 rows, 993 plays, 2 games`.

---

## Phase 5 — MySQL write, script, dump, your own analysis (≈2 hrs) [→ R4–R8, T1]

### 5.1 — `get_conn()` + `write_table()` [→ R4, R5, R7]

One generic writer handles every table — the deliverable and the three source tables you'll need for the validation SQL.

- [ ] **Do (a) — `get_conn()`.** `mysql.connector.connect(...)` with `host, port, user, password, database` from `os.environ` (names in `.env.example`). `int()` the port. Nothing hard-coded → R7.
- [ ] **Do (b) — DDL strings.** Four module-level strings: `DDL` for `pbp_players_on_court` (the schema in `CLAUDE.md`, verbatim — indexes included), and `DDL_PBP`, `DDL_PBP_PLAYERS`, `DDL_ROSTERS` from `docs/source-table-ddl.md`. Column names must match the frames exactly.
- [ ] **Do (c) — `write_table(df, table, ddl, conn, key="event_id")`.** Build the `INSERT` from `df.columns`. Convert `NaN → None` and numpy scalars → Python with `df.astype(object).where(df.notna(), None)`. Then, in one cursor: execute the DDL; **per game** `DELETE … WHERE key = %s` then `executemany`. One `commit()`. Return `len(df)`.
**Why:** Delete-then-insert per game = a rerun makes the table *equal* the source, orphans included (an upsert wouldn't). One commit = all-or-nothing per call. mysql-connector runs non-autocommit, so a failure before `commit()` leaves the table untouched — that's R5 in one sentence for the writeup. Building the `INSERT` from the columns is what lets one function load all four tables.

<details><summary>Skeleton</summary>

```python
def get_conn():
    """MySQL connection from .env — nothing hard-coded."""

    conn = mysql.connector.connect(
        host=os.environ["MYSQL_HOST"],
        port=int(os.environ["MYSQL_PORT"]),
        user=os.environ["MYSQL_USER"],
        password=os.environ["MYSQL_PASSWORD"],
        database=os.environ["MYSQL_DATABASE"],
    )
    return conn


def write_table(df: pd.DataFrame, table: str, ddl: str, conn, key: str = "event_id") -> int:
    """Create `table` if needed, then replace each game's rows. Returns rows written."""

    cols = ", ".join(df.columns)
    marks = ", ".join(["%s"] * len(df.columns))
    insert_sql = f"INSERT INTO {table} ({cols}) VALUES ({marks})"

    clean = df.astype(object).where(df.notna(), None)  # NaN -> NULL, numpy scalars -> Python
    with conn.cursor() as cur:
        cur.execute(ddl)
        for eid, game in clean.groupby(key):
            cur.execute(f"DELETE FROM {table} WHERE {key} = %s", (int(eid),))
            cur.executemany(insert_sql, game.to_numpy().tolist())
    conn.commit()
    return len(df)
```

`ndarray.tolist()` returns native Python types, which is what fixes the connector's "Python 'int64' cannot be converted to a MySQL type" error. `with conn.cursor()` closes the cursor; the caller's `with get_conn() as conn:` closes the connection — including on failure, which discards the uncommitted transaction.

</details>

- [ ] **Run cell** (Docker up — `docker compose ps` says healthy):

```python
with get_conn() as conn:
    print("pbp_players_on_court", write_table(on_court[OUT_COLS], "pbp_players_on_court", DDL, conn))
    print("pbp                 ", write_table(pbp, "pbp", DDL_PBP, conn))
    print("pbp_players         ", write_table(pbpp, "pbp_players", DDL_PBP_PLAYERS, conn))
    print("rosters             ", write_table(ros, "rosters", DDL_ROSTERS, conn))
```

**You should see:** `9930`, `1011`, `1284`, `66`.

- [ ] **Run it again.** Same four numbers. Then confirm nothing doubled:

```python
def query(sql: str) -> pd.DataFrame:
    """Run a query against the docker MySQL, return a DataFrame."""

    with get_conn() as conn:
        result = pd.read_sql(sql, conn)
    return result


query("SELECT 'on_court' t, COUNT(*) n FROM pbp_players_on_court UNION ALL SELECT 'pbp', COUNT(*) FROM pbp")
```

**You should see:** `9930` and `1011` — not `19860` / `2022`. **That's R5.** Paste both outputs into the walkthrough.

`pd.read_sql` prints a `UserWarning` about SQLAlchemy — harmless. Silence once in setup: `warnings.filterwarnings("ignore", message="pandas only supports SQLAlchemy")`.

<details><summary>If not</summary>

- `InterfaceError: 2003 Can't connect` → Docker isn't up, or `.env` port ≠ compose port. `docker compose ps`.
- `ProgrammingError: 1045 Access denied` → `.env` password ≠ what the container was *created* with. If you changed `.env` after first `up`: `docker compose down -v` then `up -d` (wipes the volume; the script rebuilds everything).
- `ProgrammingError: 1054 Unknown column 'x'` → a frame column isn't in that table's DDL, or is spelled differently. Compare `df.columns` to the DDL.
- `DataError: 1264 Out of range` → a `TINYINT`/`SMALLINT` is too small for a value in a new game. Widen the type in the DDL, `DROP TABLE`, rerun.
- `TypeError ... nan can not be used with MySQL` → the `.where(df.notna(), None)` step is missing.
- `KeyError: 'MYSQL_HOST'` → `load_dotenv()` didn't find `.env`. Notebook cwd must be the repo root (`os.getcwd()`).

</details>

---

### 5.2 — `sql/validation.sql`: points while on court [→ T1 — their tip]

The PDF's one tip: *"summing up the total team points scored while each player was on court … try doing your own calculations on the new data set."* Two queries. The first is the analysis; the second proves the table is right.

**Why the join works:** `pbp` has one row per play with `play_team_id` (who scored) and `points_scored`. `pbp_players_on_court` has ten rows per play. Join on `(event_id, play_id)` and every point gets attached to the ten players on the floor — five for, five against.

- [ ] **Do (a) — Query 1, per player.** Join `pbp_players_on_court oc` to `pbp p` on `(event_id, play_id)`. For each `(event_id, team_id, player_id)`: `pts_for` = sum of `points_scored` where `p.play_team_id = oc.team_id`; `pts_against` = where it isn't; `plays` = `COUNT(DISTINCT p.play_id)`. Order by `pts_for` desc.
- [ ] **Do (b) — Query 2, reconciliation.** Every point a team scores lands on exactly five of its players, so `SUM(pts_for)` across a team's players must equal **5 ×** the team's total in `pbp`. Per `(event_id, team_id)`: `on_court_pts` from query 1 vs `5 * SUM(points_scored)` from `pbp` where `play_team_id = team_id`, and the difference.
- [ ] **Do (c) — save both to `sql/validation.sql`**, then run them from the notebook with `query(...)`.

<details><summary>Skeleton</summary>

```sql
-- Query 1: team points scored for / against while each player was on court
SELECT
  oc.event_id,
  oc.team_id,
  oc.player_id,
  r.name,
  SUM(CASE WHEN p.play_team_id =  oc.team_id THEN p.points_scored ELSE 0 END) AS pts_for,
  SUM(CASE WHEN p.play_team_id <> oc.team_id THEN p.points_scored ELSE 0 END) AS pts_against,
  COUNT(DISTINCT p.play_id)                                                 AS plays
FROM pbp_players_on_court oc
JOIN pbp     p ON p.event_id = oc.event_id AND p.play_id = oc.play_id
JOIN rosters r ON r.event_id = oc.event_id AND r.player_id = oc.player_id
GROUP BY oc.event_id, oc.team_id, oc.player_id, r.name
ORDER BY pts_for DESC;
```

```sql
-- Query 2: reconciliation — on-court points must be exactly 5x the team's total
WITH on_court_pts AS (
  SELECT oc.event_id, oc.team_id,
         SUM(CASE WHEN p.play_team_id = oc.team_id THEN p.points_scored ELSE 0 END) AS on_court_pts
  FROM pbp_players_on_court oc
  JOIN pbp p ON p.event_id = oc.event_id AND p.play_id = oc.play_id
  GROUP BY oc.event_id, oc.team_id
),
team_pts AS (
  SELECT event_id, play_team_id AS team_id, SUM(points_scored) AS team_pts
  FROM pbp
  GROUP BY event_id, play_team_id
)
SELECT o.event_id, o.team_id, t.team_pts, 5 * t.team_pts AS expected, o.on_court_pts,
       o.on_court_pts - 5 * t.team_pts AS diff
FROM on_court_pts o
JOIN team_pts t ON t.event_id = o.event_id AND t.team_id = o.team_id
ORDER BY o.event_id, o.team_id;
```

`points_scored` is `NULL` on non-scoring plays; `SUM` ignores `NULL`, and the `CASE … ELSE 0` keeps the arithmetic clean.

</details>

- [ ] **Run cell:**

```python
query(open("sql/validation.sql").read().split(";")[0])      # query 1
```
```python
query(open("sql/validation.sql").read().split(";")[1])      # query 2
```

(`split(";")` is fine here because neither query has a semicolon inside it. If you'd rather not depend on that, keep the two queries in two files.)

**You should see, query 2:**

| event_id | team_id | team_pts | expected | on_court_pts | diff |
|---|---|---|---|---|---|
| 1947160 | 2 | 92 | 460 | 460 | 0 |
| 1947160 | 9 | 88 | 440 | 440 | 0 |
| 1947312 | 10 | 142 | 710 | 710 | 0 |
| 1947312 | 21 | 116 | 580 | 580 | 0 |

`team_pts` matches the final scores in `pbp` (BOS 92–88 GS; HOU 142–116 PHO). **Query 1** tops out with Trevor Ariza `pts_for = 111`, James Harden `108`, Ryan Anderson `95` — all Houston, all in the 142-point game.

**Paste query 2 into the walkthrough.** It's a one-table proof that every lineup has exactly five players from the scoring team on every scoring play.

<details><summary>If not</summary>

- `diff ≠ 0` for a team → a lineup somewhere has the wrong count for that team on a scoring play. `validate()` should have caught it; if `validate` passes and this doesn't, the `pbp` table is stale — rerun 5.1's write cell.
- `Unknown table 'pbp'` → 5.1's write cell hasn't run.
- `team_pts` ≠ final score → `points_scored` loaded as `0` instead of `NULL`, or `pbp` has duplicate rows (PK would have rejected them — so probably the former). Check `query("SELECT COUNT(*) FROM pbp WHERE points_scored IS NULL")` → 770.
- Query 1 rows ≠ 40-ish (players who saw the floor) → `rosters` join dropped someone; `query("SELECT COUNT(*) FROM rosters")` → 66.

</details>

---

### 5.3 — Move the notebook into `on_court.py` [→ R1, R6, R7]

The deliverable is a script. Do this once, now that everything works.

- [ ] **Do (a):** In VS Code, notebook toolbar → `...` → **Export** → **Python Script**. Save over `on_court.py`. Then clean it: delete the run cells (anything that's not an `import`, a constant, a function, or the DDL/INSERT strings), delete the `# %%` comments if you like, keep the function order.
- [ ] **Do (b):** Add `main()` at the bottom — `argparse` with `--game` (required, `"all"` or an event_id), `--validate`, `--no-db`, `--load-source`. Load → filter to one game if asked (all three frames; error cleanly if the id isn't in `pbp`) → `attach_roster_team` → `openers` → `subs` → `walk_plays` → `validate` if asked → `write_table` for `pbp_players_on_court` unless `--no-db`; the three source tables too if `--load-source` → print one summary line. `if __name__ == "__main__": sys.exit(main())`.

<details><summary>Skeleton</summary>

```python
def main() -> int:
    ap = argparse.ArgumentParser(description="Derive the 10 players on court for every play.")
    ap.add_argument("--game", required=True, help='an event_id, or "all"')
    ap.add_argument("--validate", action="store_true", help="run integrity checks before writing")
    ap.add_argument("--no-db", action="store_true", help="build and validate only; skip MySQL")
    ap.add_argument("--load-source", action="store_true", help="also load pbp / pbp_players / rosters (for validation.sql)")
    args = ap.parse_args()

    pbp, pbpp, ros = load(DATA_DIR)
    if args.game != "all":
        eid = int(args.game)
        if eid not in set(pbp.event_id):
            print(f"error: event_id {eid} not found in pbp", file=sys.stderr)
            return 1
        pbp, pbpp, ros = pbp[pbp.event_id == eid], pbpp[pbpp.event_id == eid], ros[ros.event_id == eid]

    pbpp = attach_roster_team(pbpp, ros)
    openers = period_openers(pbpp)
    subs = sub_events(pbpp)
    on_court = walk_plays(pbp, openers, subs)

    if args.validate:
        validate(on_court, pbp, ros)
    if not args.no_db:
        with get_conn() as conn:
            n = write_table(on_court[OUT_COLS], "pbp_players_on_court", DDL, conn)
            if args.load_source:
                write_table(pbp, "pbp", DDL_PBP, conn)
                write_table(pbpp, "pbp_players", DDL_PBP_PLAYERS, conn)
                write_table(ros, "rosters", DDL_ROSTERS, conn)
        print(f"wrote {n} rows for {on_court.event_id.nunique()} game(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

</details>

- [ ] **Run the sequence from the terminal and record every output** (all five go in the walkthrough):

```bash
python on_court.py --game 1947160
```
→ `wrote 4890 rows for 1 game(s)`
```bash
python on_court.py --game all --validate
```
→ `validate: 5/5 passed ...` then `wrote 9930 rows for 2 game(s)`
```bash
python on_court.py --game all
```
→ `wrote 9930 ...` again; SQL count still 9930 — **idempotent**
```bash
python on_court.py --game 999
```
→ `error: event_id 999 not found in pbp`, exit code 1, no traceback
```bash
python on_court.py --game all --no-db --validate
```
→ validate passes, nothing written — proves the script runs without a DB

- [ ] **`test_on_court.py`** (optional, 20 min now that imports work): `from on_court import *`; module-scoped fixture calling `load(DATA_DIR)`; tests: Booker → 21; `openers` 16 groups of 5; P1 self-test; `walk_plays` → 9930; a hand-built 3-play frame with one sub. `pytest -q`.

---

### 5.4 — The dump deliverable [→ R8]

Dump inside the container, copy the file out — avoids PowerShell's redirect-encoding problem. **Single quotes** on the outer string: PowerShell leaves `$` alone inside them, so `sh` in the container expands `$MYSQL_ROOT_PASSWORD` (with double quotes PowerShell hands over a literal `\$` and MySQL says `Access denied`):

```bash
docker exec swish-mysql sh -c 'mysqldump -u root -p"$MYSQL_ROOT_PASSWORD" swish pbp_players_on_court --result-file=/tmp/dump.sql'
```
```bash
docker cp swish-mysql:/tmp/dump.sql sql/pbp_players_on_court.sql
```

- [ ] Open it: one `CREATE TABLE`, a few big `INSERT INTO ... VALUES (...),(...)` statements, ~400–600 KB.
- [ ] **Prove it restores.** PowerShell strips inner double quotes from native-command arguments, so `mysql -e "..."` breaks; pipe the SQL in on stdin instead (`docker exec -i` lets stdin through):

```bash
"CREATE DATABASE swish_check" | docker exec -i swish-mysql sh -c 'mysql -u root -p"$MYSQL_ROOT_PASSWORD"'
```
```bash
docker exec swish-mysql sh -c 'mysql -u root -p"$MYSQL_ROOT_PASSWORD" swish_check < /tmp/dump.sql'
```
```bash
"SELECT COUNT(*) FROM swish_check.pbp_players_on_court; DROP DATABASE swish_check" | docker exec -i swish-mysql sh -c 'mysql -u root -p"$MYSQL_ROOT_PASSWORD"'
```

→ `9930`. The `[Warning] Using a password on the command line` lines are expected.

**✅ Done when:** the five terminal runs behave as listed, the dump restores to 9930, and the reconciliation difference is 0.

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
