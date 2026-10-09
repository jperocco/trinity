# Annual identity and source reconciliation

## Findings

Matched 1,723 of 1,891 supplied season rows to unique nflverse player IDs (91.1%). Exact normalized name plus position resolves 1,698 rows; unique suffix variants resolve another 25. No fuzzy or nickname matching is applied. Unmatched rows remain unresolved, including positional differences and players absent from the stat-row reference.

The unresolved identity count among otherwise backtest-eligible rows is only 17 of 1,481 (1.15%). That is below the agreed 4% relevance threshold; further alias investigation is paused. This percentage describes identity exclusions only, not the much larger next-season eligibility/survivorship exclusions.

Among 1,721 uniquely matched, nonduplicate rows:

- Receptions, receiving yards and receiving touchdowns all agree except five season rows. Taysom Hill 2023 is the substantial discrepancy: FP has 10 games / 23 receptions / 200 yards / one receiving TD; nflverse has 16 stat weeks / 33 receptions / 291 yards / two receiving TDs. Smaller differences involve Rashid Shaheed 2022 and receiving yards for Ladd McConkey, Pat Freiermuth and Eric Saubert in 2024.
- Targets and air yards frequently disagree. Preserve FP targets/shares/routes together; do not substitute nflverse numerator or denominator values into those shares.
- 1,373 total FP values agree with nflverse PPR within 0.051 (79.8%). All available matched FP/G values agree with FP divided by source G within one-decimal rounding tolerance. Cross-provider scoring remains different for some players; no universal scoring correction is inferred.
- Source G often exceeds the number of nflverse stat weeks. Stat rows are not a complete games-played ledger, so they cannot replace source G. Source G is smaller for Taysom Hill 2023 and Bo Melton 2025; both are explicitly flagged.

These checks establish a traceable ID mapping and identify discrepancies. They do not certify FP route definitions, team-share denominators, scoring, or full-season scope for every source row.

## Stable-ID sensitivity

Reusing the same temporal split and alpha grid, matching on nflverse ID plus FP position produces 841 transitions: 405 training, 218 validation and 218 final-test pairs. This is an audit sensitivity after the original holdout was inspected, not a second untouched test.

| Forecast, combined model | 2025 MAE |
|---|---:|
| Calibrated prior FP/G | 2.230 |
| Target share alone | 2.190 |
| Three shares | 2.195 |
| Three shares + prior FP/G | 2.176 |

The original conclusion remains: no compelling annual advantage for a fixed three-share composite. Removing the one matched transition involving Taysom Hill's anomalous 2023 export changes the three-share MAE from 2.195 to 2.191. It does not alter that conclusion. The duplicate/extreme-share and small count-discrepancy cases remain flagged without modifying the original archive.

## Reproduce

With the local nflverse files described by the acquisition audit:

```sh
python scripts/reconcile_annual.py
python scripts/backtest_annual.py --crosswalk docs/FP_PLAYER_CROSSWALK.json --report docs/ANNUAL_BACKTEST_STABLE_IDS.json
python -m unittest discover -s tests
```

Outputs: `ANNUAL_RECONCILIATION.json`, `FP_PLAYER_CROSSWALK.json`, `ANNUAL_BACKTEST_STABLE_IDS.json` and `ANNUAL_BACKTEST_SENSITIVITY.json`. Tests check temporal holdout independence, position separation, paired uncertainty sign, and deterministic name normalization. Total test suite: 21 passing tests.

Weekly historical FP or PFF route exports are still needed for weekly validation. The annual route percentages cannot reconstruct weekly route opportunity counts. The current 2026 JJ snapshot has only four final weeks, insufficient for the existing complete three-week lookback plus three-week future-outcome test. Keep a weekly composite experimental until usable historical data arrives.
