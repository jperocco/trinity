# Expansão de features: previsão de PPR futuro

Same complete-case sample for every model, six-plus games in both seasons. StandardScaler + Ridge alpha=10 fixed, fitted only on outcome years before each test year. Outcomes 2023, 2024, 2025; features always from previous season. Predictions clipped at zero. Prior-PPR comparator is a fitted one-feature ridge, not raw persistence.

Todas as métricas abaixo são MAE em PPR/jogo; menor é melhor. Pooled pondera cada observação igualmente.

| Posição | Modelo | 2023 | 2024 | 2025 | Pooled | Ganhos vs core | Δ vs core (IC95%) |
|---|---|---:|---:|---:|---:|---:|---|
| WR | core | 2.721 | 2.897 | 2.290 | 2.635 | 0/3 | +0.000 [+0.000, +0.000] |
| WR | efficiency | 2.699 | 2.930 | 2.342 | 2.657 | 1/3 | +0.022 [-0.083, +0.124] |
| WR | quality | 2.835 | 2.896 | 2.280 | 2.669 | 2/3 | +0.034 [-0.008, +0.076] |
| WR | full | 2.771 | 2.922 | 2.339 | 2.677 | 0/3 | +0.042 [-0.064, +0.146] |
| WR | prior_ppr | 2.715 | 2.868 | 2.357 | 2.647 | 2/3 | +0.011 [-0.106, +0.131] |
| TE | core | 1.873 | 1.916 | 1.888 | 1.893 | 0/3 | +0.000 [+0.000, +0.000] |
| TE | efficiency | 1.826 | 1.906 | 1.818 | 1.850 | 3/3 | -0.043 [-0.088, +0.002] |
| TE | quality | 1.885 | 1.900 | 1.887 | 1.891 | 2/3 | -0.002 [-0.034, +0.029] |
| TE | full | 1.829 | 1.892 | 1.825 | 1.849 | 3/3 | -0.044 [-0.105, +0.016] |
| TE | prior_ppr | 1.827 | 1.891 | 1.998 | 1.908 | 2/3 | +0.015 [-0.087, +0.115] |

## Composição dos modelos

- **core**: targets_per_game, target_share
- **efficiency**: targets_per_game, target_share, yprr, yard_share
- **quality**: targets_per_game, target_share, air_yard_share, redzone_targets_per_game, endzone_targets_per_game
- **full**: targets_per_game, target_share, yprr, yard_share, air_yard_share, redzone_targets_per_game, endzone_targets_per_game, routes_per_game, route_share
- **prior_ppr**: prior_ppr

## Limitações

- Exploratory: 2025 and earlier results have already been inspected; these are not untouched holdouts.
- Annual next-season predictions do not validate next-week predictions or weekly weights.
- Bootstrap resamples player identities together across folds; intervals are conditional on these three seasons, not uncertainty over future seasons.
- Eligibility in both years introduces survivorship; source identity is provisional.
- YPRR uses source YDS/RTE, shares use source percentages, and red-zone/end-zone counts can overlap.
- JJ lacks complete quality inputs; no missing values are replaced by zero.

## Decisão

Manter o core atual (targets/jogo + target share) para WR e TE. WR piora no agregado com todos os blocos adicionais. TE melhora nos três cortes com eficiência, mas apenas 0,043 PPR/jogo (~2,3%); o IC95% da diferença inclui zero. O modelo completo tem ganho semelhante com mais entradas e maior incerteza. Eficiência fica como candidata para TE, sem promoção por enquanto. Não há evidência de superioridade clara sobre o comparador de PPR anterior. Esta análise não altera o painel nem os coeficientes congelados.
