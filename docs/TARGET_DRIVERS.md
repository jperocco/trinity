# Targets as the path to future points

Source: supplied Fantasy Points annual 2021–2025 exports only. Eligible rows: 943 WR and 538 TE. No external source joins or corrections. This study reframes the objective around future fantasy points, rather than similarity to another product's ranking.

## Current-season associations

Spearman correlations across eligible player-season rows, not causal effects:

| Indicator | WR targets/G | TE targets/G |
|---|---:|---:|
| Target share | 0.991 | 0.994 |
| Yard share | 0.963 | 0.968 |
| Routes/G | 0.946 | 0.963 |
| Route share | 0.944 | 0.960 |
| Targets/route | 0.622 | 0.631 |

Targets/G = routes/G × targets/route by definition. Both opportunity and earning targets matter; correlation of one factor alone does not establish which sustains future targets. Target share also contains the targets being explained. Do not treat these same-season correlations as forecasts. Season totals were converted to per-game values to avoid simply measuring games played.

## Future-season targets and points

Same source name-position matching; at least six games in both seasons. Ridge alpha=10 fixed for every candidate, scaling fitted only to training data. Train outcomes 2022–2024; evaluate outcomes in 2025 (132 WR, 86 TE). 2025 was already inspected in earlier analyses; this is exploratory, not a new untouched holdout. All candidates within position use the same sample.

Mean absolute error, lower is better:

| Prior-season inputs | WR future targets/G | TE future targets/G | WR future FP/G | TE future FP/G |
|---|---:|---:|---:|---:|
| Prior FP/G | 1.105 | 0.963 | 2.357 | 1.998 |
| Routes/G | 1.333 | 0.845 | 2.865 | 1.940 |
| Route share | 1.292 | 0.830 | 2.816 | 1.867 |
| Target share | 1.056 | 0.869 | 2.380 | 1.883 |
| Targets/G | 1.028 | 0.884 | 2.313 | 1.937 |
| Yard share | 1.095 | 0.901 | 2.401 | 1.833 |
| Targets/G + target share | 1.004 | 0.869 | 2.290 | 1.888 |
| Above + routes/G + route share | 1.007 | 0.836 | 2.294 | 1.855 |
| Volume/relevance + air share + red-zone/G + end-zone/G | 1.000 | 0.866 | 2.280 | 1.887 |

For WR, earned volume and team relevance outperform routes alone in this future-year experiment. Adding target-quality variables produces only a small point-estimate improvement. For TE, routes carry stronger future-target signal; adding routes to volume/relevance improves the point estimate. Do not conclude the small MAE differences are established improvements: paired 95% bootstrap intervals for the expanded models versus prior FP/G include zero in both positions.

Yard share strongly associates with current-season FP/G (WR 0.975; TE 0.968), but it includes realized receiving yards, a direct scoring component. It is useful as lagged production/context, not evidence that current opportunity alone explains future scoring. It forecasts 2025 TE FP/G well in this sample but does not outperform WR volume/relevance. YPRR alone is weaker than volume/relevance for future points in both positions.

## Engine implication

Keep targets/G and target share as the WR volume/relevance core. Treat route exposure as sustainability/context and target depth/red-zone/end-zone usage as additional candidate information. Test position-specific point forecasts, not a universal share average. Yard share and YPRR are separate lagged efficiency/production candidates. Compare every expansion against prior FP/G and simpler volume baselines.

Targets are not worth identical points: receptions, yards and touchdowns determine realized receiving points, while red-zone/end-zone/depth describe possible value. The available fields do not measure quarterback accuracy, catch probability or every feature of target quality. Red-zone and end-zone targets can overlap; do not add them as if independent opportunities.

Annual data can guide engine architecture but cannot establish optimal weekly weights. JJ 2026 supplies the weekly follow-up. Current v0.1 70/5/25 and 80/20/0 remains a frozen experimental comparison, not the validated final points model.

Run `python scripts/study_target_drivers.py`. Full metrics, correlations, feature definitions and conditional paired uncertainty are in `TARGET_DRIVERS.json`.
