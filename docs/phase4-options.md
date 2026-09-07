# Phase 4 — four versions of `walk_plays()`

All four take the same three frames and return the same 9,930-row table. All four
were run against the real data and agree row-for-row. Pick one.

## Shared prelude

`sub_events()` needs `period` in its pivot index for versions 2 and 3 (harmless for the others). This is the only change to it:

```python
def sub_events(pbpp: pd.DataFrame) -> pd.DataFrame:
    """One row per substitution: event_id, play_id, period, team_id, player_in, player_out."""

    subs = pbpp[pbpp.play_event == "Substitution"]
    wide = (
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
    wide.columns.name = None
    return wide[["event_id", "play_id", "period", "team_id", "player_in", "player_out"]]
```

Every version also uses:

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

And the same run cell:

```python
subs = sub_events(pbpp)
on_court = walk_plays(pbp, openers, subs)
print(on_court.shape, "| 10 per play:", (on_court.groupby(["event_id", "play_id"]).size() == 10).all())
on_court[(on_court.event_id == 1947160) & on_court.play_id.between(40, 42)].merge(ros[["event_id", "player_id", "name"]])
```

**You should see:** `(9930, 6) | 10 per play: True`, and Tatum on court at play 40, Smart from 41 on.

---

## Version 0 — what the plan has now: loop per game, detect period change

```python
def walk_plays(pbp: pd.DataFrame, openers: pd.DataFrame, subs: pd.DataFrame) -> pd.DataFrame:
    """One row per (play, on-court player): 10 rows per play."""

    plays = pbp[["event_id", "play_id", "period"]].drop_duplicates().sort_values(["event_id", "play_id"])
    opener_sets = openers.groupby(["event_id", "period", "team_id"]).player_id.apply(set).to_dict()
    sub_at = {(s.event_id, s.play_id): (s.team_id, s.player_in, s.player_out) for s in subs.itertuples()}

    rows = []
    for eid, game_plays in plays.groupby("event_id"):
        teams = {team for (game, _, team) in opener_sets if game == eid}
        on_court, prev_period = {}, None

        for play in game_plays.itertuples(index=False):
            if play.period != prev_period:
                on_court = {t: set(opener_sets[(eid, play.period, t)]) for t in teams}  # set(...) = copy
                prev_period = play.period

            if (eid, play.play_id) in sub_at:
                team, player_in, player_out = sub_at[(eid, play.play_id)]
                on_court[team].remove(player_out)
                on_court[team].add(player_in)

            for team, players in on_court.items():
                rows.extend((eid, play.play_id, p, team, play.period) for p in players)

    long = pd.DataFrame(rows, columns=OUT_COLS[:-1])
    return add_is_home(long, pbp)
```

| | |
|---|---|
| state | dict of two sets, plus `prev_period` |
| lookups | 2 dicts built up front |
| gotchas | must copy sets on reset; must track period change yourself; must derive `teams` |
| reads like | a scorekeeper watching the whole game |

---

## Version 1 — loop per (game, period)

The period reset *is* the top of the loop. No `prev_period`, no branch.

```python
def walk_plays(pbp: pd.DataFrame, openers: pd.DataFrame, subs: pd.DataFrame) -> pd.DataFrame:
    """One row per (play, on-court player): each period replayed from its openers."""

    plays = pbp[["event_id", "play_id", "period"]].drop_duplicates().sort_values(["event_id", "play_id"])
    opener_sets = openers.groupby(["event_id", "period", "team_id"]).player_id.apply(set).to_dict()
    sub_at = {(s.event_id, s.play_id): (s.team_id, s.player_in, s.player_out) for s in subs.itertuples()}

    rows = []
    for (eid, per), period_plays in plays.groupby(["event_id", "period"]):
        on_court = {t: set(five) for (game, p, t), five in opener_sets.items() if game == eid and p == per}

        for play in period_plays.itertuples(index=False):
            if (eid, play.play_id) in sub_at:
                team, player_in, player_out = sub_at[(eid, play.play_id)]
                on_court[team].remove(player_out)
                on_court[team].add(player_in)

            for team, players in on_court.items():
                rows.extend((eid, play.play_id, p, team, per) for p in players)

    long = pd.DataFrame(rows, columns=OUT_COLS[:-1])
    return add_is_home(long, pbp)
```

| | |
|---|---|
| state | dict of two sets |
| lookups | 2 dicts |
| gotchas | none of the three above; fresh sets every period by construction |
| reads like | a scorekeeper, one quarter at a time |

---

## Version 2 — loop per (game, period, team)

Each team's five is independent of the other's, so replay one team at a time. State is a single `set`. No dicts at all — `openers.groupby` hands you each five, `subs` and `plays` are filtered to match.

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

| | |
|---|---|
| state | one `set` |
| lookups | none — three boolean filters instead |
| gotchas | `team_subs.at[...]` assumes one sub per team per play (true here; a `.loc` + loop handles the general case) |
| reads like | "for each five that started a quarter, replay that quarter" |
| cost | filters `plays` 16 times and `subs` 16 times — microseconds |

---

## Version 3 — no loop: stints, then an interval join

Reframe the problem. A player is on court for a **stint** `[start_play, end_play)`. Stints start at a period's first play (openers) or a sub-in; they end at a sub-out or the period's last play. Build the stints table, then join every play to the stints that contain it.

```python
STINT_KEY = ["event_id", "period", "team_id", "player_id"]


def stints(plays: pd.DataFrame, openers: pd.DataFrame, subs: pd.DataFrame) -> pd.DataFrame:
    """One row per continuous on-court spell: [start_play, end_play) within a period."""

    bounds = plays.groupby(["event_id", "period"]).play_id.agg(first="min", last="max").reset_index()

    opener_starts = openers.merge(bounds, on=["event_id", "period"]).rename(columns={"first": "play_id"})
    sub_starts = subs.rename(columns={"player_in": "player_id"})
    sub_ends = subs.rename(columns={"player_out": "player_id"})

    starts = pd.concat([opener_starts, sub_starts])[STINT_KEY + ["play_id"]].assign(kind="start")
    ends = sub_ends[STINT_KEY + ["play_id"]].assign(kind="end")

    events = pd.concat([starts, ends]).sort_values(STINT_KEY + ["play_id"])
    events["end_play"] = events.groupby(STINT_KEY).play_id.shift(-1)  # each start's end is the next event

    spells = events[events.kind == "start"].merge(bounds, on=["event_id", "period"])
    spells["end_play"] = spells.end_play.fillna(spells["last"] + 1).astype(int)  # still on at the buzzer
    result = spells.rename(columns={"play_id": "start_play"})[STINT_KEY + ["start_play", "end_play"]]
    return result.reset_index(drop=True)


def walk_plays(pbp: pd.DataFrame, openers: pd.DataFrame, subs: pd.DataFrame) -> pd.DataFrame:
    """One row per (play, on-court player): plays joined to the stints that contain them."""

    plays = pbp[["event_id", "play_id", "period"]].drop_duplicates().sort_values(["event_id", "play_id"])
    spells = stints(plays, openers, subs)

    joined = plays.merge(spells, on=["event_id", "period"])
    on = joined[(joined.start_play <= joined.play_id) & (joined.play_id < joined.end_play)]
    long = on[["event_id", "play_id", "player_id", "team_id", "period"]]
    return add_is_home(long, pbp)
```

| | |
|---|---|
| state | none |
| loops | none |
| gotchas | relies on start/end alternating per player-period (true when subs are consistent — and `validate()` catches it if not); the `plays × stints` join is 993 × ~200 before filtering — small |
| reads like | interval math: "which spells contain this play?" |
| bonus | `stints` is a real table — one row per on-court spell — and the "if I had more time" item in the writeup plan. Points-per-stint, lineup plus/minus, minutes played all fall out of it. |

The "sub takes effect on its own play row" convention is exactly `start_play <= play_id < end_play`.

---

## Side by side

| | 0 per game | 1 per period | 2 per team | 3 stints |
|---|---|---|---|---|
| lines in `walk_plays` | 20 | 16 | 15 | 9 (+14 in `stints`) |
| Python loops | 2 nested | 2 nested | 2 nested | 0 |
| state | dict + prev_period | dict | one set | none |
| dict lookups | 2 | 2 | 0 | 0 |
| copy-the-set trap | yes | no | no | n/a |
| extra artifact | | | | stints table |
| explain in 30 s | hard | ok | easy | needs "interval" once |

**Recommendation:** 2 if you want the loop, 3 if you want the table. Either is a clear improvement on 0.

Plan 4.2 shows Version 0. Say which and I'll swap that one section.
