# %%

import argparse
import os
import sys

import mysql.connector
import pandas as pd
from dotenv import load_dotenv

load_dotenv()


# %%

DATA_DIR = "data"
SUB_IN = 1
SUB_OUT = 2
STARTING_LINEUP_PLAY_ID = 1
PLAYERS_PER_TEAM = 5
TECHNICAL = "Technical"


# %%

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


def load(data_dir: str = DATA_DIR) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Read the three xlsx files, cast ids to int, sort by play"""

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
def attach_roster_team(pbpp: pd.DataFrame, ros: pd.DataFrame) -> pd.DataFrame:
    """Overwrite pbpp team_id with the roster team_id"""

    roster_team = ros.set_index(["event_id", "player_id"])["team_id"].rename(
        "roster_team_id"
    )
    out = pbpp.join(roster_team, on=["event_id", "player_id"])
    out["team_id"] = out.pop("roster_team_id").astype(int)
    return out


# %%
OPENER_COLS = ["event_id", "period", "team_id", "player_id"]


def period_openers(pbpp: pd.DataFrame) -> pd.DataFrame:
    """Five on the floor at the start of each period"""

    starters = pbpp.loc[pbpp.play_id == STARTING_LINEUP_PLAY_ID, OPENER_COLS]

    evidence = pbpp[(pbpp.period >= 2) & (pbpp.play_detail != TECHNICAL)]
    first_row = evidence.drop_duplicates(subset=OPENER_COLS, keep="first")
    checked_in = (first_row.play_event == "Substitution") & (
        first_row.sequence == SUB_IN
    )
    inferred = first_row.loc[~checked_in, OPENER_COLS]

    openers = pd.concat([starters, inferred], ignore_index=True)
    return openers


# %%
def sub_events(pbpp: pd.DataFrame) -> pd.DataFrame:
    """One row per sub with player_in and player_out"""

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
    return pivoted[
        ["event_id", "play_id", "period", "team_id", "player_in", "player_out"]
    ]


# %%
OUT_COLS = ["event_id", "play_id", "player_id", "team_id", "period", "is_home"]


def add_is_home(long: pd.DataFrame, pbp: pd.DataFrame) -> pd.DataFrame:
    """Add is_home from pbp home_team_id"""

    home = pbp[["event_id", "home_team_id"]].drop_duplicates()
    out = long.merge(home, on="event_id")
    out["is_home"] = (out.team_id == out.home_team_id).astype(int)
    result = out[OUT_COLS].sort_values(OUT_COLS[:4]).reset_index(drop=True)
    return result


# %%


def walk_plays(
    pbp: pd.DataFrame, openers: pd.DataFrame, subs: pd.DataFrame
) -> pd.DataFrame:
    """One row per play per on-court player"""

    plays = (
        pbp[["event_id", "play_id", "period"]]
        .drop_duplicates()
        .sort_values(["event_id", "play_id"])
    )

    rows = []
    for (eid, per, team), five in openers.groupby(["event_id", "period", "team_id"]):
        on_court = set(five.player_id)
        team_subs = subs[
            (subs.event_id == eid) & (subs.period == per) & (subs.team_id == team)
        ].set_index("play_id")
        period_plays = plays[(plays.event_id == eid) & (plays.period == per)]

        for play in period_plays.itertuples(index=False):
            if play.play_id in team_subs.index:
                out_id = team_subs.at[play.play_id, "player_out"]
                if out_id not in on_court:
                    raise ValueError(
                        f"game {eid} period {per} team {team} play {play.play_id}: "
                        f"player {out_id} subbed out but was not on court"
                    )
                on_court.remove(out_id)
                on_court.add(team_subs.at[play.play_id, "player_in"])

            rows.extend((eid, play.play_id, p, team, per) for p in on_court)

    long = pd.DataFrame(rows, columns=OUT_COLS[:-1])
    return add_is_home(long, pbp)


# %%
def validate(on_court: pd.DataFrame, pbp: pd.DataFrame, ros: pd.DataFrame) -> None:
    """Sanity checks on the output table"""

    for eid, g in pbp.groupby("event_id"):
        missing = set(g.play_id) - set(
            on_court.loc[on_court.event_id == eid, "play_id"]
        )
        assert not missing, f"game {eid} missing play_ids {sorted(missing)[:5]}"

    per_play = on_court.groupby(["event_id", "play_id"]).size()
    assert (per_play == 2 * PLAYERS_PER_TEAM).all(), "not 10 players on every play"

    per_team = on_court.groupby(["event_id", "play_id", "team_id"]).size()
    assert (per_team == PLAYERS_PER_TEAM).all(), "not 5 per team on every play"

    on_roster = on_court.merge(
        ros[["event_id", "player_id"]], how="left", indicator=True
    )
    assert (on_roster._merge == "both").all(), "player not on roster"

    dupes = on_court.duplicated(["event_id", "play_id", "player_id"]).sum()
    assert dupes == 0, f"{dupes} duplicate rows"

    print(
        f"validate passed: {len(on_court)} rows, {len(per_play)} plays, {on_court.event_id.nunique()} games"
    )


# %%
DDL = """
CREATE TABLE IF NOT EXISTS pbp_players_on_court (
  event_id   INT        NOT NULL,
  play_id    INT        NOT NULL,
  player_id  INT        NOT NULL,
  team_id    INT        NOT NULL,
  period     INT        NOT NULL,
  is_home    INT        NOT NULL,
  updated_at TIMESTAMP  NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (event_id, play_id, player_id),
  KEY ix_player (event_id, player_id),
  KEY ix_team   (event_id, team_id, play_id)
)
"""


# %%
DDL_PBP = """
CREATE TABLE IF NOT EXISTS pbp (
  season           INT          NOT NULL,
  date             DATE         NOT NULL,
  event_id         INT          NOT NULL,
  home_team_id     INT          NOT NULL,
  home_team_abbr   VARCHAR(5)   NOT NULL,
  away_team_id     INT          NOT NULL,
  away_team_abbr   VARCHAR(5)   NOT NULL,
  play_id          INT          NOT NULL,
  play_sequence    INT          NOT NULL,
  period           INT          NOT NULL,
  clock_minutes    INT          NOT NULL,
  clock_seconds    INT          NOT NULL,
  sec_left         INT          NOT NULL,
  play_team_id     INT          NOT NULL,
  points_scored    INT              NULL,
  play_event_id    INT          NOT NULL,
  play_event       VARCHAR(40)      NULL,
  play_detail_id   INT              NULL,
  play_detail      VARCHAR(60)      NULL,
  is_blocked       INT          NOT NULL,
  distance         INT          NOT NULL,
  is_fast_break    INT              NULL,
  is_in_the_paint  INT              NULL,
  is_off_turnover  INT              NULL,
  is_second_chance INT              NULL,
  away_score       INT          NOT NULL,
  home_score       INT          NOT NULL,
  away_fouls       INT          NOT NULL,
  home_fouls       INT          NOT NULL,
  play_text        VARCHAR(255) NOT NULL,
  PRIMARY KEY (event_id, play_id, play_sequence),
  KEY ix_pbp_team (event_id, play_team_id, play_id)
)
"""

# %%
DDL_PBP_PLAYERS = """
CREATE TABLE IF NOT EXISTS pbp_players (
  season           INT          NOT NULL,
  date             DATE         NOT NULL,
  event_id         INT          NOT NULL,
  home_team_id     INT          NOT NULL,
  home_team_abbr   VARCHAR(5)   NOT NULL,
  away_team_id     INT          NOT NULL,
  away_team_abbr   VARCHAR(5)   NOT NULL,
  play_id          INT          NOT NULL,
  play_sequence    INT          NOT NULL,
  period           INT          NOT NULL,
  clock_minutes    INT          NOT NULL,
  clock_seconds    INT          NOT NULL,
  player_id        INT          NOT NULL,
  first_name       VARCHAR(40)  NOT NULL,
  last_name        VARCHAR(40)  NOT NULL,
  team_id          INT          NOT NULL,
  team_abbr        VARCHAR(5)   NOT NULL,
  score            INT              NULL,
  fouls            INT              NULL,
  sequence         INT          NOT NULL,
  position_id      INT              NULL,
  position_abbr    VARCHAR(2)       NULL,
  points_scored    INT              NULL,
  play_event_id    INT          NOT NULL,
  play_event       VARCHAR(40)      NULL,
  play_detail_id   INT              NULL,
  play_detail      VARCHAR(60)      NULL,
  is_blocked       INT          NOT NULL,
  distance         INT          NOT NULL,
  is_fast_break    INT              NULL,
  is_in_the_paint  INT              NULL,
  is_off_turnover  INT              NULL,
  is_second_chance INT              NULL,
  away_score       INT          NOT NULL,
  home_score       INT          NOT NULL,
  away_fouls       INT          NOT NULL,
  home_fouls       INT          NOT NULL,
  play_text        VARCHAR(255) NOT NULL,
  PRIMARY KEY (event_id, play_id, play_sequence, player_id),
  KEY ix_pbpp_player (event_id, player_id, play_id),
  KEY ix_pbpp_event  (event_id, play_event)
)
"""

# %%
DDL_ROSTERS = """
CREATE TABLE IF NOT EXISTS rosters (
  season           INT          NOT NULL,
  date             DATE         NOT NULL,
  event_id         INT          NOT NULL,
  team_id          INT          NOT NULL,
  team_abbr        VARCHAR(5)   NOT NULL,
  opp_id           INT          NOT NULL,
  opp_abbr         VARCHAR(5)   NOT NULL,
  home             INT          NOT NULL,
  primary_pos_id   INT          NOT NULL,
  primary_pos_abbr VARCHAR(2)   NOT NULL,
  player_id        INT          NOT NULL,
  name             VARCHAR(60)  NOT NULL,
  PRIMARY KEY (event_id, player_id),
  KEY ix_ros_team (event_id, team_id)
)
"""


# %%
def get_conn():
    """Connection from .env"""

    conn = mysql.connector.connect(
        host=os.environ["MYSQL_HOST"],
        port=int(os.environ["MYSQL_PORT"]),
        user=os.environ["MYSQL_USER"],
        password=os.environ["MYSQL_PASSWORD"],
        database=os.environ["MYSQL_DATABASE"],
    )
    return conn


def write_table(
    df: pd.DataFrame, table: str, ddl: str, conn, key: str = "event_id"
) -> int:
    """Create table if needed, then delete and reinsert by game"""

    cols = ", ".join(df.columns)
    marks = ", ".join(["%s"] * len(df.columns))
    insert_sql = f"INSERT INTO {table} ({cols}) VALUES ({marks})"

    clean = df.astype(object).where(df.notna(), None)
    with conn.cursor() as cur:
        cur.execute(ddl)
        for eid, game in clean.groupby(key):
            cur.execute(f"DELETE FROM {table} WHERE {key} = %s", (int(eid),))
            cur.executemany(insert_sql, game.to_numpy().tolist())
    conn.commit()
    return len(df)


# %%
def main() -> int:
    ap = argparse.ArgumentParser(
        description="Derive the 10 players on court for every play."
    )
    ap.add_argument("--game", required=True, help='an event_id, or "all"')
    ap.add_argument(
        "--validate", action="store_true", help="run integrity checks before writing"
    )
    ap.add_argument(
        "--no-db", action="store_true", help="build and validate only; skip MySQL"
    )
    ap.add_argument(
        "--load-source",
        action="store_true",
        help="also load pbp / pbp_players / rosters (for the queries in sql/)",
    )
    args = ap.parse_args()

    pbp, pbpp, ros = load(DATA_DIR)
    if args.game != "all":
        try:
            eid = int(args.game)
        except ValueError:
            print(
                f'error: --game must be an event_id or "all", got {args.game!r}',
                file=sys.stderr,
            )
            return 1
        if eid not in set(pbp.event_id):
            print(f"error: event_id {eid} not found in pbp", file=sys.stderr)
            return 1
        pbp, pbpp, ros = (
            pbp[pbp.event_id == eid],
            pbpp[pbpp.event_id == eid],
            ros[ros.event_id == eid],
        )

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


# %%
if __name__ == "__main__":
    sys.exit(main())
