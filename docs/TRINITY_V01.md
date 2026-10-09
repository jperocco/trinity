# Trinity v0.1 — weights created from the supplied data

Use only supplied Fantasy Points annual exports for 2021–2025 and JJ Stats for 2026. No nflverse identity mapping, statistics, or corrections are used in this calibration. Existing source archives remain unchanged.

## Weekly candidate for the intended product

The next-week experiment uses JJ's one-week shares to rank next-week PPR. On weeks 1→2 and 2→3, search 231 nonnegative combinations on a five-percentage-point grid, with weights summing to one. Select maximum Spearman rank correlation, then keep weights fixed for week 3→4. Results are exploratory: the split was chosen after looking at broader weekly summaries, only three transitions exist, and repeated players create dependence.

| Position | Route share | Target share | Air yard share | Development observations | Week 3→4 observations |
|---|---:|---:|---:|---:|---:|
| WR | 70% | 5% | 25% | 247 | 118 |
| TE | 80% | 20% | 0% | 161 | 73 |

These are the provisional weekly candidates, not established ideal weights. They maximize ranking association within the development sample; they do not minimize point-projection error or demonstrate causal component importance.

### Week 3 usage → week 4 PPR rank correlation

Higher is better.

| Input | WR | TE |
|---|---:|---:|
| Weekly candidate | 0.395 | 0.681 |
| Route share alone | **0.411** | 0.672 |
| Target share alone | 0.338 | 0.637 |
| Air yard share alone | 0.272 | 0.592 |
| Week 3 PPR | 0.355 | 0.481 |

The WR composite does not beat route share alone on this transition. TE composite beats it by only 0.009. There is no claim of a robust composite improvement, so retain route-only as a visible benchmark and do not freeze these weights as final.

## What the annual sheets establish

For a same-season opportunity/production fit, use all 1,481 eligible source rows (943 WR, 538 TE), with at least six source-defined games, complete features/FP/G, unique source name-position, and no >100% air-yard-share anomaly. Negative air-yard shares are preserved. Fit an intercept plus nonnegative least-squares coefficients, then normalize the three coefficients to sum to one. No minimum component weight is forced.

| Position | Route | Target | Air yards |
|---|---:|---:|---:|
| WR annual descriptive fit | 0% | 100% | 0% |
| TE annual descriptive fit | 1.83% | 95.94% | 2.23% |

Leaving one season out keeps WR target weight between 99.32% and 100%, and TE between 94.52% and 96.82%. This is a stable annual result, but it answers a different question from next-week opportunity. Annual shares and annual production are contemporaneous; their association is not a future-week forecast.

The difference is useful: annual output emphasizes earned targets; the short weekly snapshot favors route participation as an indicator of the next game's opportunity. That explanation is an interpretation of these results, not a demonstrated causal mechanism.

## Score formula and application

Use source share fractions in the formula:

```text
WR weekly candidate = 100 × (0.70 × route_share + 0.05 × target_share + 0.25 × air_yard_share)
TE weekly candidate = 100 × (0.80 × route_share + 0.20 × target_share)
```

For 80% routes, 20% targets and 30% air yards, WR score is 64.5; TE score is 68.0. These are weighted percentage points, not percentiles or predicted PPR. Compare within position. Unusual source shares are not clipped. Equal percentage-point input units mean displayed weight percentages are not variance explained.

Applied both annual-baseline and weekly-candidate scores to 937 JJ player-game rows covering weeks 1–4. Local ignored outputs are `data/processed/trinity_v01/jj_trinity_v01_weekly.csv` and `jj_trinity_v01_forward.csv`. Private JJ player records are not published. Name + team + position identifies JJ histories internally; trades split histories. Missing weeks/PPR are not imputed.

The report also evaluates annual-fixed weights on one-, two- and three-week JJ windows. Longer-window shares are ratios of summed numerators to summed denominators, not averages of percentages. Future outcomes are strictly week +1. These checks do not fit on JJ outcomes; the weekly candidate search is separately labeled and explicitly does.

## Reproduce and continue

```sh
python -m pip install -r requirements-annual.txt
python scripts/calibrate_trinity.py
python -m unittest discover -s tests
```

Full weights, rolling annual checks, leave-one-season-out stability and initial JJ weekly results: `TRINITY_V01_CALIBRATION.json`. The script does not need nflverse assets or crosswalks. Without a local JJ canonical CSV it produces annual calibration only. All 24 current tests pass.

Keep these weekly candidate weights fixed for the next unobserved weeks. Compare them with route-only, target-only and prior-PPR baselines before changing weights. As 2026 grows, use calendar-time training/validation splits and broader past/future windows, with a persistent record of which weeks were already inspected. The short current snapshot supports a first candidate and monitoring, not a definitive optimum.
