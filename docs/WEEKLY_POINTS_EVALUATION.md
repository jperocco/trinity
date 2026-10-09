# Validação semanal do score congelado

Frozen FP annual-trained equation, no JJ fitting or weight selection. Cutoffs 1,2,3 predict observed PPR in calendar weeks 2,3,4. Consolidated inputs use only records at or before cutoff. Identical adjacent-observation sample for all comparisons. MAE compares annual-equivalent points reference with weekly PPR; 0–10 score itself is not in PPR units. Targets evaluated by rank correlation only, not a points conversion.

| Posição | Modelo | MAE PPR | Spearman |
|---|---|---:|---:|
| WR | score_consolidated | 5.194 | 0.490 |
| WR | score_last_week | 5.764 | 0.399 |
| WR | ppr_consolidated | 5.709 | 0.431 |
| WR | ppr_last_week | 6.490 | 0.354 |
| WR | targets_consolidated | — | 0.480 |
| WR | targets_last_week | — | 0.382 |
| TE | score_consolidated | 4.004 | 0.534 |
| TE | score_last_week | 4.164 | 0.483 |
| TE | ppr_consolidated | 4.421 | 0.497 |
| TE | ppr_last_week | 4.968 | 0.429 |
| TE | targets_consolidated | — | 0.537 |
| TE | targets_last_week | — | 0.480 |

## Cortes cronológicos

| Posição | Corte → semana prevista | N | MAE score consolidado | MAE PPR consolidado |
|---|---|---:|---:|---:|
| WR | 1–1 → 2 | 125 | 5.320 | 6.010 |
| WR | 1–2 → 3 | 122 | 4.943 | 5.388 |
| WR | 1–3 → 4 | 118 | 5.321 | 5.720 |
| TE | 1–1 → 2 | 88 | 4.015 | 4.711 |
| TE | 1–2 → 3 | 73 | 4.546 | 4.716 |
| TE | 1–3 → 4 | 73 | 3.450 | 3.775 |

## Incerteza e cobertura

- WR: 365 pares, 148 jogadores; 65 de 430 observações de origem sem registro na semana seguinte. Δ MAE score − PPR consolidado: -0.515, IC95% [-0.877, -0.170].
- TE: 234 pares, 96 jogadores; 38 de 272 observações de origem sem registro na semana seguinte. Δ MAE score − PPR consolidado: -0.416, IC95% [-0.736, -0.127].

## Limitações

- Only three prediction origins, conditional on players with observed rows in both adjacent weeks; missing rows are not zeros.
- Annual-trained model has not been calibrated for weekly outcomes. Current JJ archive is retrospective, not a real-time historical snapshot.
- Player-cluster bootstrap does not capture team/game dependence or season-to-season uncertainty.
- Pooled rank correlations mix prediction weeks; per-origin results are also reported.
- This is exploratory: JJ weeks have been inspected in prior work. No coefficients or UI changed.

## Decisão

Manter pesos congelados e consolidado como visão principal. O score consolidado reduz MAE versus PPR consolidado em 9,0% para WR e 9,4% para TE, com ganho nos três cortes. Também supera a última semana isolada. A ordenação acrescenta pouco a targets/jogo consolidado: Spearman WR 0,490 versus 0,480; TE 0,534 versus 0,537. Ainda não é prova de benefício de target share além de targets, nem validação externa. Próxima avaliação: repetir os mesmos comparadores com novas semanas JJ, antes de ajustar recência ou coeficientes. Nenhuma mudança no painel.
