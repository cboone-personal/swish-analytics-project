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