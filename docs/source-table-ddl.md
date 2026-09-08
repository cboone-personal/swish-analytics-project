# Reference DDL for the three source tables

Types and nullability are from profiling the actual files (2026-09-06). These are
dev-convenience tables so `sql/validation.sql` can join to `pbp`; they are not the
deliverable table. Write them into your notebook / `sql/` yourself.

Conventions matching `pbp_players_on_court`: `INT` for every integer column,
`NULL` only where the file actually has blanks,
backticks on `date` (MySQL keyword).

## pbp — one row per play (1,011 rows; `play_id 1` is 10 rows)

```sql
CREATE TABLE IF NOT EXISTS pbp (
  season           SMALLINT     NOT NULL,
  `date`           DATE         NOT NULL,
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
  sec_left         SMALLINT     NOT NULL,
  play_team_id     INT          NOT NULL,
  points_scored    INT              NULL,   -- NULL on non-scoring plays (770 of 1011)
  play_event_id    INT          NOT NULL,
  play_event       VARCHAR(40)      NULL,   -- NULL on the 20 Starting Lineup rows
  play_detail_id   SMALLINT         NULL,
  play_detail      VARCHAR(60)      NULL,
  is_blocked       INT          NOT NULL,
  distance         INT          NOT NULL,
  is_fast_break    INT              NULL,   -- NULL on Starting Lineup rows
  is_in_the_paint  INT              NULL,
  is_off_turnover  INT              NULL,
  is_second_chance INT              NULL,
  away_score       SMALLINT     NOT NULL,
  home_score       SMALLINT     NOT NULL,
  away_fouls       INT          NOT NULL,
  home_fouls       INT          NOT NULL,
  play_text        VARCHAR(255) NOT NULL,
  PRIMARY KEY (event_id, play_id, play_sequence),
  KEY ix_pbp_team (event_id, play_team_id, play_id)
);
```

The PK prefix `(event_id, play_id)` is what `pbp_players_on_court` joins on — no extra index needed for that.

## pbp_players — one row per player involved in a play (1,284 rows after dropping team-event rows)

Written **after** `attach_roster_team()`, so `team_id` is the roster's.

```sql
CREATE TABLE IF NOT EXISTS pbp_players (
  season           SMALLINT     NOT NULL,
  `date`           DATE         NOT NULL,
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
  team_id          INT          NOT NULL,   -- roster team, not the feed's
  team_abbr        VARCHAR(5)   NOT NULL,   -- feed's; wrong on play 149 (Booker) — keep for the writeup
  score            INT              NULL,   -- player's running points; NULL on 346 rows
  fouls            INT              NULL,
  sequence         INT          NOT NULL,   -- role in the play: sub 1=in 2=out; foul 1=committer 3=fouled; etc.
  position_id      INT              NULL,   -- only on Starting Lineup rows
  position_abbr    VARCHAR(2)       NULL,
  points_scored    INT              NULL,
  play_event_id    INT          NOT NULL,
  play_event       VARCHAR(40)      NULL,
  play_detail_id   SMALLINT         NULL,
  play_detail      VARCHAR(60)      NULL,
  is_blocked       INT          NOT NULL,
  distance         INT          NOT NULL,
  is_fast_break    INT              NULL,
  is_in_the_paint  INT              NULL,
  is_off_turnover  INT              NULL,
  is_second_chance INT              NULL,
  away_score       SMALLINT     NOT NULL,
  home_score       SMALLINT     NOT NULL,
  away_fouls       INT          NOT NULL,
  home_fouls       INT          NOT NULL,
  play_text        VARCHAR(255) NOT NULL,
  PRIMARY KEY (event_id, play_id, play_sequence, player_id),
  KEY ix_pbpp_player (event_id, player_id, play_id),
  KEY ix_pbpp_event  (event_id, play_event)
);
```

`player_id` is in the PK so it stays unique even if a feed reuses `play_sequence` within a play.

## rosters — one row per player per game (66 rows)

```sql
CREATE TABLE IF NOT EXISTS rosters (
  season           SMALLINT     NOT NULL,
  `date`           DATE         NOT NULL,
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
);
```

`(event_id, player_id)` is the join `attach_roster_team()` and `validate()` use.

## Loading them

`write_table()` works unchanged for all three — pass the frame, the table name, and `key="event_id"`. `date` arrives as a pandas Timestamp; the connector writes it into `DATE` fine (time part is 00:00 in this data). `NaN` → `NULL` via the `.where(df.notna(), None)` step.

Two things to watch:

- `pbp_players.team_id` **must** come from the post-`attach_roster_team` frame or the validation join will put Booker on Houston.
- If you hand-write these DDLs *and* keep `ddl_from_frame()`, use one or the other per table — `CREATE TABLE IF NOT EXISTS` won't alter a table that already exists with different types. `DROP TABLE` first when switching.
