# Phase 3 — three ways to get the period openers

> **Update (2026-09-06):** the `period >= 2` filter and `starting_five()` are unnecessary.
> The same rule handles Q1 — the Starting Lineup rows at `play_id 1` are each starter's
> first row and aren't sub-ins. Verified: with no period filter, 16 groups × 5. Every
> version below is shown without the filter; `starting_five()` and the `concat` are gone.

All three produce the same 80-row frame `openers[event_id, period, team_id, player_id]`
(16 groups × 5, all four periods). All three were run against the real data and agree row-for-row.
Pick one, type it, delete the others from your head.

## Shared prelude (same for every version)

You have `load()`. (`player_team_map()`, `home_team_map()`, `game_teams()` are not needed
in this design — delete them.) One more piece every version needs:

```python
import numpy as np   # only Version B uses it

OPENER_COLS = ["event_id", "period", "team_id", "player_id"]


def attach_roster_team(pbpp: pd.DataFrame, ros: pd.DataFrame) -> pd.DataFrame:
    """Overwrite pbpp.team_id with the roster's team_id. Fixes the one bad row (Booker, play 149)."""

    roster_team = ros.set_index(["event_id", "player_id"])["team_id"].rename("roster_team_id")
    out = pbpp.join(roster_team, on=["event_id", "player_id"])
    out["team_id"] = out.pop("roster_team_id").astype(int)
    return out

```

Run cell after these:

```python
pbpp = attach_roster_team(pbpp, ros)
pbpp.loc[pbpp.play_id == 149, ["last_name", "team_abbr", "team_id"]]   # Booker: Hou / 21
```

Every version below starts from the same filtered frame — technicals removed, **all periods**:

```python
later = pbpp[pbpp.play_detail != TECHNICAL]
```

`pbpp` is already sorted by `(event_id, play_id, play_sequence)` from `load()`. Versions A and C depend on that.

---

## Version A — "What's the first thing he did?"  *(recommended)*

**Idea:** for each player in each period, look at the **first row** he appears in.
If that row is him checking in (`Substitution`, `sequence == SUB_IN`), he started on the bench.
Anything else — a shot, a rebound, a foul, getting subbed *out* — means he was already on the floor.

```python
def period_openers(pbpp: pd.DataFrame) -> pd.DataFrame:
    """Who was on the floor at the start of each period: first appearance isn't a sub-in."""

    later = pbpp[pbpp.play_detail != TECHNICAL]
    first_row = later.drop_duplicates(subset=OPENER_COLS, keep="first")
    checked_in = (first_row.play_event == "Substitution") & (first_row.sequence == SUB_IN)
    openers = first_row.loc[~checked_in, OPENER_COLS].reset_index(drop=True)
    return openers
```

**Run / verify:**

```python
openers = period_openers(pbpp)
openers.groupby(["event_id", "period", "team_id"]).size().reset_index(name="players")   # 16 rows, all 5
```

To *see* the reasoning for one team-period, look at `first_row` for Boston Q2 before you wrap it in the function:

```python
first_row[(first_row.event_id == 1947160) & (first_row.period == 2) & (first_row.team_id == 2)][
    ["player_id", "last_name", "play_id", "play_event", "sequence", "play_text"]
]
```

You'll see Baynes' first row is a rebound at 118 (opener), Morris' first row is "Substitution … in" at 129 (not).

| | |
|---|---|
| **Lines** | 4 |
| **Loops** | none |
| **Depends on** | frame being sorted by play order; `drop_duplicates(keep="first")` keeps the earliest |
| **Best for** | shortest code, reads exactly like the sentence it implements |
| **Weak spot** | the rule is implicit in "first row" — reviewer has to think for a second |

---

## Version B — "First seen vs first subbed in"

**Idea:** same rule, made explicit as two numbers per player. `first_seen` = earliest `play_id`
of any evidence (subbed out, or any non-sub event). `first_in` = earliest `play_id` he was
subbed in. Opener if `first_seen < first_in`; never subbed in counts as infinity.

```python
def period_openers(pbpp: pd.DataFrame) -> pd.DataFrame:
    """Openers per period: first seen before first subbed in."""

    later = pbpp[pbpp.play_detail != TECHNICAL]
    is_sub = later.play_event == "Substitution"

    sub_in = later[is_sub & (later.sequence == SUB_IN)]
    evidence = later[(is_sub & (later.sequence == SUB_OUT)) | ~is_sub]

    first_in = sub_in.groupby(OPENER_COLS).play_id.min().rename("first_in")
    first_seen = evidence.groupby(OPENER_COLS).play_id.min().rename("first_seen")
    firsts = pd.concat([first_seen, first_in], axis=1)

    opened = firsts[firsts.first_seen < firsts.first_in.fillna(np.inf)]
    openers = opened.reset_index()[OPENER_COLS]
    return openers
```

**Run / verify:** same as A. The extra payoff is `firsts` — a frame with the two columns side by side:

```python
firsts.loc[(1947160, 2, 2)]      # Boston, Q2: player_id -> first_seen, first_in
```

| | |
|---|---|
| **Lines** | 9 |
| **Loops** | none |
| **Depends on** | `play_id` increasing through the game (it does) — doesn't need the frame sorted |
| **Best for** | the writeup: `firsts` is a screenshot that explains the rule by itself |
| **Weak spot** | two filters that must be complementary; `fillna(np.inf)` needs a sentence |

---

## Version C — "Read the period like a human"

**Idea:** for each `(game, period, team)`, walk its rows in order with a `subbed_in` set.
A player who does anything before he's in that set was on the floor. This is the
row-by-row scan, but scoped to one small group at a time and returned as a list, so
pandas does the bookkeeping instead of nested loops.

```python
def _scan_openers(group: pd.DataFrame) -> list[int]:
    """One (game, period, team): players seen before being subbed in."""

    subbed_in, openers = set(), set()
    for row in group.itertuples(index=False):
        if row.play_event == "Substitution" and row.sequence == SUB_IN:
            subbed_in.add(row.player_id)
        elif row.player_id not in subbed_in:
            openers.add(row.player_id)
    return sorted(openers)


def period_openers(pbpp: pd.DataFrame) -> pd.DataFrame:
    """Openers per period: scan each team-period in play order."""

    later = pbpp[pbpp.play_detail != TECHNICAL]
    per_group = later.groupby(["event_id", "period", "team_id"]).apply(_scan_openers, include_groups=False)
    openers = per_group.explode().rename("player_id").reset_index().astype(int)
    return openers[OPENER_COLS]
```

**Run / verify:** same as A. To see one group's reasoning, call the helper directly:

```python
g = later[(later.event_id == 1947160) & (later.period == 2) & (later.team_id == 2)]
_scan_openers(g)
```

| | |
|---|---|
| **Lines** | 12 (two functions) |
| **Loops** | one, per team-period, over ~60 rows |
| **Depends on** | frame sorted by play order |
| **Best for** | matches how you'd explain it out loud; the helper is trivially unit-testable with a 3-row frame |
| **Weak spot** | `groupby().apply()` + `explode()` is the fiddliest pandas here; slowest of the three (irrelevant at this size) |

---

## Then, identically for all three

```python
openers = period_openers(pbpp)
counts = openers.groupby(["event_id", "period", "team_id"]).size().reset_index(name="players")
print("all 5:", (counts.players == 5).all())      # True
counts                                             # 16 rows of 5
```

If any group is **6** → Trap 1 or Trap 2 leaked (check `attach_roster_team` ran; check `TECHNICAL` is in the filter).
If any group is **4** → you're excluding real evidence (only technicals go).

---

## Which one

| | A first-row | B two-mins | C group-scan |
|---|---|---|---|
| shortest | ✔ | | |
| clearest in the writeup | | ✔ | |
| closest to how you'd say it | | | ✔ |
| no ordering assumption | | ✔ | |
| easiest to unit-test | | | ✔ |

**A** for the code. Keep B's `firsts` snippet as a one-off notebook cell for the walkthrough screenshot. C is what you say in the interview when they ask "how does it work" — then point at A and say "same rule, vectorised."

`docs/plan.md` 3.3 uses **A**. Swap in B or C there if you prefer — the run cells and checks are identical.
