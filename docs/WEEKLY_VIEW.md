# Weekly explorer

The offline explorer reads JJ canonical records and fixed `models/trinity_weekly_v01.json` weights. It does not recalibrate weights, call external services, or combine providers. The generated HTML contains private JJ data and stays outside the public repository.

Run from the repository root:

```sh
python scripts/build_weekly_view.py
```

Open `data/processed/Trinity_Weekly.html` in a browser. All data, styling and interactions are embedded; no server or login is needed. Regenerate after importing a new JJ snapshot.

Features: week and position filters, one-week or trailing-three-week shares, player/team search, sortable score/share/PPR table, delta against the immediately prior week, individual weekly score/PPR history, and descriptive usage/production quartile signals.

Three-week windows require consecutive observed calendar weeks. Shares use ratios of sums. Incomplete windows show their actual number of observations and receive no usage/production signal. Missing weeks and PPR are not filled with zero. Histories are separate by source name, team, position and season; trades split them.

Signal rules compare within the available position-week cohort before search filters: usage percentile at least 75% with PPR percentile at most 25%, or the inverse. Tied observations use average percentile rank. These labels describe the snapshot and are not a forecast of a bounce-back or decline. Score and PPR in the history chart have different units and share a numeric axis; that distinction is explicitly labeled.

Frozen provisional weights: WR 70/5/25 and TE 80/20/0 for routes/targets/air yards. Scores are weighted percentage points, not percentiles or PPR projections. The weekly candidate has not demonstrated a robust advantage over route-only. Keep the route and target shares visible beside it.
