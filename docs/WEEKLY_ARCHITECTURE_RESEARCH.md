# Pesquisa semanal: oportunidade antes de pontos

No refitting of upstream XFP model (documented training 2006–2020). Our standardized ridge alpha=10 fixed. Test seasons 2023,2024,2025, trained only on earlier seasons. Within-season features through cutoff; minimum 3 observed source games; actual adjacent-calendar-week outcome required, same player and team. Recent window is 3 calendar weeks, missing observations never zero-filled. Common complete-case sample. Outcome is receiving-only PPR, excluding rushing and return points. XFP reconstructed in same PPR units, without expected fumble penalty. Zero-target history aDOT convention =0, not a missing-field imputation.

| Posição | Alvo | Modelo | 2023 MAE | 2024 MAE | 2025 MAE | Agregado MAE |
|---|---|---|---:|---:|---:|---:|
| WR | future_targets | target_mean | 2.084 | 2.154 | 2.136 | 2.124 |
| WR | future_targets | target_core | 2.081 | 2.139 | 2.136 | 2.118 |
| WR | future_targets | target_context | 2.066 | 2.126 | 2.119 | 2.103 |
| WR | future_ppr | ppr_mean | 5.093 | 5.180 | 5.133 | 5.135 |
| WR | future_ppr | ppr_last | 6.420 | 6.822 | 6.458 | 6.565 |
| WR | future_ppr | ppr_prior_fitted | 5.062 | 5.207 | 5.105 | 5.124 |
| WR | future_ppr | ppr_direct_core | 5.098 | 5.190 | 5.115 | 5.134 |
| WR | future_ppr | ppr_direct_context | 5.090 | 5.161 | 5.118 | 5.123 |
| WR | future_ppr | ppr_xfp_mean | 5.020 | 5.139 | 5.115 | 5.090 |
| WR | future_ppr | ppr_xfp_fitted | 5.043 | 5.179 | 5.112 | 5.110 |
| WR | future_ppr | ppr_two_stage | 5.122 | 5.204 | 5.103 | 5.143 |
| TE | future_targets | target_mean | 1.717 | 1.877 | 1.712 | 1.768 |
| TE | future_targets | target_core | 1.714 | 1.898 | 1.706 | 1.772 |
| TE | future_targets | target_context | 1.718 | 1.885 | 1.710 | 1.770 |
| TE | future_ppr | ppr_mean | 4.004 | 4.238 | 4.296 | 4.182 |
| TE | future_ppr | ppr_last | 5.150 | 5.347 | 5.652 | 5.388 |
| TE | future_ppr | ppr_prior_fitted | 4.062 | 4.330 | 4.343 | 4.247 |
| TE | future_ppr | ppr_direct_core | 3.955 | 4.270 | 4.270 | 4.168 |
| TE | future_ppr | ppr_direct_context | 3.949 | 4.280 | 4.289 | 4.176 |
| TE | future_ppr | ppr_xfp_mean | 3.962 | 4.232 | 4.193 | 4.131 |
| TE | future_ppr | ppr_xfp_fitted | 3.990 | 4.271 | 4.276 | 4.181 |
| TE | future_ppr | ppr_two_stage | 3.954 | 4.254 | 4.238 | 4.151 |



## Cobertura e incerteza

- WR: 3802 previsões; Δ MAE XFP médio − PPR médio -0.045, IC95% [-0.107, +0.017].
- TE: 1797 previsões; Δ MAE XFP médio − PPR médio -0.051, IC95% [-0.107, +0.005].

## Limitações

- Conditional on source rows in both origin and future week: absence is not proof of inactivity or zero targets.
- No routes in these weekly tables; route-based target-earning hypothesis remains untested.
- Two-stage conversion uses only prior-season positional receiving points per target; not a learned target-quality model.
- Cluster bootstrap groups players across weeks; team/game dependence is not captured.
- Public historical XFP files are retrospective; train-period documentation does not guarantee historical real-time availability.
- Repeated candidate comparisons make this exploratory; no score or production coefficients changed.

## Decisão

Não promover uma nova fórmula. XFP médio tem o menor MAE agregado entre os candidatos, com vantagem sobre PPR médio nos três anos para ambas as posições, mas os intervalos de diferença incluem zero. O pipeline simples de duas etapas não oferece ganho consistente sobre as referências. O próximo eixo de pesquisa é o papel das rotas e a projeção do valor dos targets, não a busca de mais combinações de shares. Não confundir XFP do ffopportunity com XFP proprietário da Fantasy Points. Os ganhos de 9% do experimento JJ não se repetem automaticamente neste histórico maior e com outro universo/scoring.

## Reprodução

Execute `python scripts/download_weekly_research.py` e `python scripts/research_weekly_architecture.py`. Requer numpy, pandas, scipy e scikit-learn. Fontes públicas e hashes constam no JSON. Somente código e resultados agregados são publicados; nenhuma união com planilhas premium ou JJ.
