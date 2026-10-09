# Trinity v0.2: future points first

The main score now derives from a future-year FP/G model trained on supplied Fantasy Points annual exports. No nflverse join or source correction is used. JJ 2026 features are applied separately to that fixed model. It is an annual-equivalent points reference, not a calibrated next-week fantasy projection.

## Selection and evaluation

Standardized ridge alpha=10 for every candidate. Train outcome years 2022–2023; choose the deployable feature block using 2024 MAE; refit through 2024 and inspect 2025. The last season was already inspected in previous experiments; this remains exploratory. Final artifact refits the selected block on all 2022–2025 pairs, with 522 WR and 323 TE transitions.

| Model | WR 2024 validation MAE | TE 2024 validation MAE | WR 2025 MAE | TE 2025 MAE |
|---|---:|---:|---:|---:|
| Targets/G + target share (selected) | 2.897 | 1.916 | 2.290 | 1.888 |
| Above + route exposure | 2.920 | 1.919 | 2.294 | 1.855 |
| Above + air share | 2.919 | 1.921 | 2.293 | 1.854 |
| Full quality research with RZ/EZ | 2.940 | 1.904 | 2.292 | 1.858 |
| Prior FP/G baseline | **2.868** | **1.891** | 2.357 | 1.998 |

The selected usage model does not beat prior FP/G in the selection season. It improves the point estimate in 2025, but paired uncertainty against the prior-PPR baseline includes zero. Do not call it an established predictive improvement. It gives a traceable usage-based points estimate that can be monitored against baselines.

Full RZ/EZ quality is annual research only. Uploaded JJ has RZ counts for 636/963 WR/TE rows and no end-zone target field; missing opportunities are not set to zero. Among deployable blocks the core wins validation for both positions; extra opportunity inputs remain visible in the UI and model comparison instead of being forced into the predictor.

## Frozen deployment equations

Shares are fractions, e.g. 30% = 0.30:

```text
WR annual-equivalent FP/G = max(0, 0.348620892 + 0.935185093 × targets/G + 22.163256935 × target_share)
TE annual-equivalent FP/G = max(0, 0.722112895 + 0.611940181 × targets/G + 29.238673447 × target_share)
score = 10 × (1 − 10^(−annual_equivalent_FP/G / anchor))
anchor WR = 15.3; anchor TE = 15.3
```

In v0.2.1, the fixed pooled WR+TE 95th percentile of eligible annual FP/G (15.3) maps to score 9 for both positions. Larger point estimates remain distinguishable below 10. The score is not a percentile, is not the DD proprietary formula, and is not comparable to an uncalibrated probability. Use the PPR/G reference for the absolute points estimate, and the shared score as a presentation scale. No manual ranking targets or screenshot scores enter the fit.

## Explorer integration

Consolidated and trailing-window targets/G use sum of targets divided by the number of observed eligible games. Share features are ratios of summed numerators and denominators. In the consolidated default, players without a final-week row remain included using their observed prior records, with game coverage and last week marked. Missing weeks never become zero. Weekly deltas now compare v0.2 scores in adjacent observed calendar weeks.

The table adds targets/G and annual-equivalent PPR/G beside observed PPR/G. Rotas and air-yard shares remain visible. v0.1 is retained in source artifacts and hidden data fields as an experimental baseline, not the primary score. The main UI explicitly labels v0.2 as annual-trained and experimental; player-game data remains private in the delivered HTML.

## Reproduce

```sh
python scripts/train_points_model.py
python scripts/build_weekly_view.py
python -m unittest discover -s tests
```

`models/trinity_points_v02.json` contains the portable coefficients, intercepts and fixed score anchors. `docs/POINTS_V02_EVALUATION.json` includes all validation/test comparisons and conditional bootstrap intervals. 33 tests pass, including numeric equivalence between fitted and exported equations, no missing-input imputation, fixed score anchors, historical-window cutoff integrity and ratios of sums. DOM checks cover the added point columns, team WR+TE mode, weekly selection and player details.

Next-week validation must use growing JJ history and an explicitly temporal split. Annual-equivalent estimates are transfer experiments until weekly calibration is demonstrated. Repeated players, survivorship, source name matching and the small number of seasons remain limitations.

## v0.2.1 comparison correction

Predictive coefficients, selected features, intercepts and FP/G estimates are unchanged. Only the score anchor is now shared across positions; identical point estimates have identical scores, so a combined WR+TE score ranking preserves the point ranking.

The explorer displays TS jogos (targets divided by team targets in eligible observed player games) and TS período (targets divided by all available team-game targets in the selected calendar interval). Team totals are counted once per team-game; they include games without that player’s row and never include future weeks. The current snapshot covers 128 team-games. These are distinct measures of active role and full-period participation. Missing individual records still do not become zero-scoring games. Full-period share uses the available recorded team games, not an inferred schedule.

The frozen equation still uses TS jogos. TS período is a separate comparison field; it has not silently replaced a trained feature. That input-definition choice remains a modeling question for later validation. Private source records are not exported to GitHub.
