# Aproximação do Trinity original

Referência: 12 jogadores visíveis no relatório fornecido, semanas 1–4. Testadas 90 combinações: 15 subconjuntos das quatro métricas, com transformação linear, teto ou logaritmo, com intercepto ou saturação ancorada em zero. Coeficientes não negativos. Seleção por erro leave-one-out; resultado exploratório.

| Transformação | Métricas | MAE | MAE leave-one-out | Spearman |
|---|---|---:|---:|---:|
| capped | target_share, yprr | 0.1269 | 0.1643 | 0.902 |
| capped | target_share, yprr, air_yard_share | 0.1248 | 0.1759 | 0.898 |
| log | target_share, yprr, air_yard_share | 0.1221 | 0.1794 | 0.853 |
| linear | target_share, yprr, air_yard_share | 0.1258 | 0.1876 | 0.842 |
| saturation_log | target_share, yprr, air_yard_share | 0.1397 | 0.1917 | 0.853 |
| capped | target_share, yprr, redzone_targets_per_game | 0.1342 | 0.1963 | 0.898 |
| saturation_capped | yprr, air_yard_share, redzone_targets_per_game | 0.1535 | 0.2029 | 0.758 |
| linear | target_share, yprr, air_yard_share, redzone_targets_per_game | 0.1261 | 0.2038 | 0.842 |

## Pesos do candidato

Pesos relativos aos componentes normalizados; o intercepto participa do score e não está nesses percentuais. Escalas TS=40%, YPRR=4, AY share=50%, RZ targets/jogo=3.

- target_share: 48.2%
- yprr: 51.8%
- air_yard_share: 0.0%
- redzone_targets_per_game: 0.0%

Intercepto: 6.1235. Transformação: capped. Erro máximo na referência: 0.3988.

## Limitações

- 12 visible top-ranked players only, including one TE; cannot establish full-universe ranking or position-specific weights.
- Leave-one-out measures interpolation within this selected report, not independent validation; candidate selection also uses these rows.
- Displayed input rounding limits identifiability; several weight combinations can fit similarly.
- Weights depend on the declared metric normalization; they are not recovered proprietary weights.
- Red-zone targets missing in JJ are never filled with zero. Reference metrics used directly to isolate formula fit from source differences.
- 0–10 clipping and nonnegative intercept/coefficients are approximation assumptions.

## Alternativa ancorada em zero

Melhor candidata que dá score zero sem oportunidade: saturation_log; MAE 0.1397; leave-one-out 0.1917.

Modelos com intercepto alto reproduzem o topo mas dão score alto sem oportunidade: não devem ser extrapolados para toda a liga. Nenhum candidato foi promovido ao painel.

Candidata ancorada: TS 36,2%; YPRR 32,2%; AY share 31,6%; RZ 0%. Esses percentuais são relativos às escalas e ao logaritmo definidos, não pesos proprietários recuperados. A ausência de RZ no ajuste não prova que o original o exclua.

Reprodução: executar `python scripts/fit_original_trinity.py` com a transcrição local `data/research/trinity_reference/top12_week4.json`. A imagem e a transcrição não foram publicadas. O JSON do relatório contém todos os candidatos, erros e coeficientes.
