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
