# Exploratory annual validation — 2021–2025

The supplied Fantasy Points exports contain 1,891 WR/TE season rows. This experiment asks whether prior-season usage forecasts next-season source-reported FP/G. It does not validate weekly predictions, PFF route definitions, or a production Trinity score.

Training outcomes: 2022 and 2023 (411 pairs). Validation outcome: 2024 (216 pairs), used to choose ridge regularization separately for each model and position. Refit through 2024 with that choice fixed. Final holdout outcome: 2025 (218 pairs: 132 WR, 86 TE). Standardization is fitted only on development data. Every model is evaluated on the same eligible sample within its position.

## Holdout mean absolute error

Lower is better; units are source-reported fantasy points per game. WR and TE columns use separately fitted models; the combined column uses a pooled model without position controls.

| Forecast | Combined | WR | TE |
|---|---:|---:|---:|
| Repeat prior FP/G | 2.429 | 2.661 | 2.074 |
| Calibrated prior FP/G | 2.213 | 2.357 | 1.998 |
| Route share only | 2.431 | 2.816 | 1.851 |
| Target share only | 2.165 | 2.380 | 1.862 |
| Air yard share only | 2.605 | 2.733 | 2.394 |
| Three usage shares | 2.170 | 2.373 | 1.838 |
| Three shares + prior FP/G | 2.159 | 2.336 | 1.923 |

## Interpretation

Target share carries most of the pooled annual signal. Three shares do not meaningfully improve on target share alone in this holdout. Their pooled MAE improvement against calibrated prior FP/G is only 0.042, with paired bootstrap 95% interval spanning a 0.189 improvement to a 0.104 deterioration. The combined four-input model also has an interval spanning zero. There is no robust pooled evidence yet for a superior three-factor composite.

Route share performs particularly well for TEs as a single annual predictor. The three-share TE model is slightly better in this holdout, but uncertainty against calibrated prior FP/G still spans zero. TE three shares plus prior FP/G improves MAE by 0.074, with a narrow conditional bootstrap interval excluding zero; this is a small, exploratory result among multiple model comparisons, not independent season replication.

Negative conditional route coefficients in the WR composite do not mean routes hurt production. Highly correlated shares measure overlapping opportunity, and these coefficients describe conditional associations. They must not become fixed intuitive score weights.

## Eligibility and limitations

- At least six source-defined games in both seasons, finite shares and FP/G, and a unique exact same-provider name plus position. Name matching is provisional and lacks certified stable player IDs.
- Both Brock Wright 2022 rows are excluded because they share name and position. They are not merged using reconstructed denominators.
- Three air-yard-share rows above 100% are flagged and excluded; negative air-yard shares are retained. No source data is modified. These duplicate/extreme-share cases are below 4% of the raw universe; further investigation is paused until they matter to a decision.
- Complete-case survivorship is substantial: 76 of 294 eligible 2024 players lack an eligible matched 2025 row. The forecast is conditional on returning and satisfying next-year eligibility, not a forecast for all current players. Rookies and career exits are not modeled.
- Rounded percentages, provider game definitions and scoring remain unreconciled. The six-game threshold was specified before evaluating the holdout; no threshold search was performed.
- The bootstrap uses 5,000 paired player resamples in 2025, not independent season resamples. One season and multiple comparisons limit conclusions.

## Reproduce

Install `requirements-annual.txt`, then run from the repository root:

```sh
python scripts/backtest_annual.py
python -m unittest tests.test_annual_backtest
```

Full audit, coefficients, errors, correlations and paired comparisons are in `ANNUAL_BACKTEST.json`. The temporal leakage test changes holdout outcomes and verifies that model coefficients and hyperparameters do not change.

Next: reconcile player identity and export semantics, then obtain weekly historical data for schedule-aware within-season validation. Keep route share and target share visible separately in the explorer while composite weights remain experimental.
