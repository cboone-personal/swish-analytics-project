# %% setup
import argparse
import os
import sys

import mysql.connector
import pandas as pd
from dotenv import load_dotenv

load_dotenv()


# %% constants

DATA_DIR = "data"
SUB_IN = 1
SUB_OUT = 2
STARTING_LINEUP_PLAY_ID = 1
PLAYERS_PER_TEAM = 5
TECHNICAL = "Technical"

# %% load function

ID_COLS_PBP = [
    "event_id",
    "play_id",
    "play_sequence",
    "period",
    "home_team_id",
    "away_team_id",
    "play_team_id",
]
ID_COLS_PBPP = [
    "event_id",
    "play_id",
    "play_sequence",
    "period",
    "player_id",
    "team_id",
]
ID_COLS_ROS = ["event_id", "team_id", "player_id"]


def load(data_dir):
    pbp = pd.read_excel(f"{data_dir}/pbp.xlsx")
    pbpp = pd.read_excel(f"{data_dir}/pbp-players.xlsx")
    ros = pd.read_excel(f"{data_dir}/rosters.xlsx")

    pbpp = pbpp[pbpp.player_id.notna()].copy()

    pbp[ID_COLS_PBP] = pbp[ID_COLS_PBP].astype(int)
    pbpp[ID_COLS_PBPP] = pbpp[ID_COLS_PBPP].astype(int)
    ros[ID_COLS_ROS] = ros[ID_COLS_ROS].astype(int)

    pbp = pbp.sort_values(["event_id", "play_id", "play_sequence"]).reset_index(
        drop=True
    )
    pbpp = pbpp.sort_values(["event_id", "play_id", "play_sequence"]).reset_index(
        drop=True
    )
    ros = ros.sort_values(["event_id", "team_id", "player_id"]).reset_index(drop=True)
    return pbp, pbpp, ros


# %%
pbp, pbpp, ros = load(DATA_DIR)

# %% lookups


def player_team_map(ros: pd.DataFrame) -> dict[tuple[int, int], int]:
    """(event_id, player_id) -> team_id"""

    ptm = ros.set_index(["event_id", "player_id"])["team_id"].to_dict()
    return ptm


def home_team_map(pbp: pd.DataFrame) -> dict[int, int]:
    """event_id -> home_team_id."""

    htm = (
        pbp.drop_duplicates("event_id").set_index("event_id")["home_team_id"].to_dict()
    )
    return htm


def game_teams(ros: pd.DataFrame) -> dict[int, set[int]]:
    """event_id -> {team_id, team_id}."""

    gt = ros.groupby("event_id")["team_id"].apply(set).to_dict()
    return gt


# %%
player_team = player_team_map(ros)
home_team = home_team_map(pbp)
game_team_set = game_teams(ros)
# %%


def period_openers(pbpp: pd.DataFrame, team_map: dict, teams_by_game: dict) -> dict:
    """(event_id, period, team_id) -> set of 5 player_ids on the floor when the period started."""
    result = {}

    for (eid, per), grp in pbpp.groupby(["event_id", "period"], sort=True):
        teams = teams_by_game[eid]

        # ---- 3.4a: period 1 is given to us ----
        if per == 1:
            starters = grp[grp.play_id == STARTING_LINEUP_PLAY_ID]
            for t in teams:
                result[(eid, 1, t)] = {
                    int(p) for p in starters.player_id if team_map[(eid, int(p))] == t
                }
            continue

        # ---- 3.4b: periods 2+ must be inferred ----
        subbed_in = {t: set() for t in teams}
        openers = {t: set() for t in teams}

        for row in grp.itertuples(
            index=False
        ):  # grp is already sorted by play_id, play_sequence
            pid = int(row.player_id)
            t = team_map[(eid, pid)]  # TRAP 1: never row.team_id

            if row.play_event == "Substitution":
                if row.sequence == SUB_IN:
                    subbed_in[t].add(pid)
                elif row.sequence == SUB_OUT and pid not in subbed_in[t]:
                    openers[t].add(pid)  # left before arriving -> was a starter
            else:
                if (
                    row.play_detail == TECHNICAL
                ):  # TRAP 2 (3.4c): techs can come from the bench
                    continue
                if pid not in subbed_in[t]:
                    openers[t].add(
                        pid
                    )  # did something before arriving -> was a starter

        for t in teams:
            result[(eid, per, t)] = openers[t]

    return result


# %%
