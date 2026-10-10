# Trinity original: ampliação para o meio do ranking

Two user-provided screenshots 2026-10-09 23:49:25 and 23:49:54; visible ranks 17–28 and 31–40

Unconfirmed cutoff; two players have GP=5. Kept separate from earlier top12 with max GP=4.

A candidata anterior, sem novo ajuste, tem MAE 0.599 e Spearman 0.513 no novo recorte. Um score constante igual à média da referência tem MAE 0.214; portanto erro numérico pequeno sozinho não garante reconstrução do ranking.

| Transformação | Componentes | MAE | Leave-one-out MAE | Spearman |
|---|---|---:|---:|---:|
| capped | air_yard_share, redzone_targets_per_game | 0.165 | 0.193 | 0.542 |
| capped | yprr, air_yard_share, redzone_targets_per_game | 0.161 | 0.196 | 0.567 |
| capped | air_yard_share | 0.179 | 0.197 | 0.468 |
| log | air_yard_share, redzone_targets_per_game | 0.169 | 0.198 | 0.515 |
| linear | air_yard_share, redzone_targets_per_game | 0.169 | 0.200 | 0.517 |
| log | yprr, air_yard_share, redzone_targets_per_game | 0.166 | 0.203 | 0.504 |
| log | air_yard_share | 0.184 | 0.204 | 0.451 |
| capped | target_share, yprr, air_yard_share, redzone_targets_per_game | 0.156 | 0.204 | 0.647 |

## Pesos da alternativa ancorada em zero

- target_share: 35.8%
- yprr: 45.9%
- air_yard_share: 5.4%
- redzone_targets_per_game: 12.9%

Transformação saturation_log; MAE 0.294; Spearman 0.548. Escalas TS=40%, YPRR=4, AY share=50%, RZ/jogo=3.

## Limitações

- 22 selected middle-ranked rows, not full league; 10 TE and 12 WR.
- The new capture includes five-game players: merging with earlier four-game snapshot would confound calibration and period changes.
- Four shown metrics do not identify all original formula inputs or normalization; leave-one-out and candidate selection use this same selected sample.
- Normalized component weights are conditional on scales and transformations, not recovered proprietary weights.
- Nonnegative models can fail to reproduce rankings even when numerical score error is small.
- No source reconciliation, position-specific correction, manual player adjustment or production model change performed.

## Decisão

A candidata anterior não está confirmada: não transferiu bem ao novo recorte. Também não adotar o ajuste de intercepto, que aproxima os números comprimindo a faixa e reproduz mal a ordem. Pesos ficam exploratórios; não alterar o painel. Reproduzir com `python scripts/fit_trinity_middle_reference.py`, usando a transcrição local `data/research/trinity_reference/middle22_new_capture.json`. Capturas e transcrição permanecem locais.
