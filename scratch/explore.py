# %% scratch / exploration
# Interactive playground. Not part of the deliverable.
# Run cells with Shift+Enter (VS Code Interactive Window).
#
# Typical use: load the frames once here, then poke at them while
# building functions in on_court.py.

# %% setup
import pandas as pd

pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 50)
pd.set_option("display.max_rows", 200)
# %% read excel files


pbp = pd.read_excel("data/pbp.xlsx")
pbpp = pd.read_excel("data/pbp-players.xlsx")
ros = pd.read_excel("data/rosters.xlsx")
pbp.shape, pbpp.shape, ros.shape
# %% pbp value counts by play_event

# pbp.play_event.value_counts(dropna=False)
pbp_counts = (
    pbp.groupby(["play_event_id", "play_event"], dropna=False)
    .size()
    .sort_values(ascending=False)
)
pbpp_counts = (
    pbpp.groupby(["play_event_id", "play_event"], dropna=False)
    .size()
    .sort_values(ascending=False)
)
# print(pbp_counts)
# print(pbpp_counts)

# %% compare play_event counts between pbp and pbpp
play_event_counts_joined = pd.concat(
    [
        pbp.play_event.value_counts().rename("pbp"),
        pbpp.play_event.value_counts().rename("pbpp"),
    ],
    axis=1,
)
play_event_counts_joined[
    play_event_counts_joined["pbpp"] > play_event_counts_joined["pbp"]
]
# %%

pbp.groupby("play_event").play_id.agg(["count", "nunique"])


# %%
pbp[pbp.play_id == 1][
    ["event_id", "play_id", "play_sequence", "play_team_id", "play_text"]
]
# %%
pbpp[pbpp.play_id == 1][
    [
        "event_id",
        "play_id",
        "play_sequence",
        "play_text",
        "player_id",
        "first_name",
        "last_name",
        "team_abbr",
        "position_abbr",
    ]
]

# %%
subs = pbpp[pbpp.play_event == "Substitution"]
subs[
    [
        "event_id",
        "play_id",
        "play_sequence",
        "first_name",
        "last_name",
        "team_abbr",
        "play_event",
        "play_text",
    ]
].head(10)
# %%
subs.groupby(["event_id", "play_id"]).size().value_counts()
# %%
bos_gsw = pbp[pbp.event_id == 1947160]
bos_gsw[bos_gsw.play_id.between(110, 125)][
    [
        "play_id",
        "period",
        "clock_minutes",
        "clock_seconds",
        "play_event",
        "play_team_id",
        "play_text",
    ]
]
# %%

team_lookup = ros.set_index(["event_id", "player_id"]).team_abbr
chk = pbpp[pbpp.player_id.notna()].join(
    team_lookup.rename("roster_team"), on=["event_id", "player_id"]
)
chk[chk.team_abbr != chk.roster_team][
    ["play_id", "first_name", "last_name", "team_abbr", "roster_team", "play_text"]
]

# %%
chk.roster_team.isna().sum()
# %%

techs = pbpp[pbpp.play_detail == "Technical"]

# %%
pbpp[(pbpp.player_id == 660085) & (pbpp.event_id == 1947312) & (pbpp.period == 4)][
    ["play_id", "clock_minutes", "clock_seconds", "play_event", "sequence", "play_text"]
]
# %%
