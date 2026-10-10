# Trinity: pesos e normalização conjuntos

Shared zero-anchored monotonic 0–10 formula; four feature weights, four normalization scales and four powers optimized jointly. 12 deterministic starts per fit; score-only versus score-plus-within-report-order objective. Reports equally weighted, kept as separate snapshots; no cross-report pair comparisons. Reciprocal transfer diagnostics fit one report and evaluate the other. They are not independent untouched validation.

| Ajuste | Recorte | MAE | Spearman | Pares na ordem correta |
|---|---|---:|---:|---:|
| score_only | top12 | 0.251 | 0.740 | 78.1% |
| score_only | middle22 | 0.337 | 0.615 | 70.9% |
| score_and_order | top12 | 0.258 | 0.768 | 79.7% |
| score_and_order | middle22 | 0.338 | 0.618 | 71.3% |

## Transferência entre recortes

| Treinamento | Avaliação | MAE | Spearman |
|---|---|---:|---:|
| top12 | middle22 | 0.629 | 0.504 |
| middle22 | top12 | 0.960 | 0.432 |

## Contradições de monotonicidade

- top12: 0 pares em que um jogador tem todas as quatro métricas maiores ou iguais, mas score menor.
- middle22: 3 pares em que um jogador tem todas as quatro métricas maiores ou iguais, mas score menor.

## Limitações

- 34 selected rows, potentially different cutoffs, no full-universe or low-score reference.
- 12 fitted parameters are flexible relative to sample size; reciprocal transfer and dominance audit are essential. No claim of recovered original weights.
- Reported weights depend on feature scales and powers; not directly comparable to earlier fixed-scale weights.
- Displayed rounding can affect dominance; selected conflicts should be checked against visible values.
- Same inputs can omit proprietary components, position normalization, thresholds or other transformations. Dominance violations rule out this monotonic four-feature family, not every possible original model.
- No individual overrides, JJ/FP source joins, model promotion or panel changes.

## Achado decisivo

No mesmo recorte, com quatro jogos cada, T.J. Hockenson tem TS 25,7%, YPRR 2,22, AY share 24,2% e 5 RZ targets; Travis Kelce tem 18,6%, 2,09, 15,6% e 2 RZ targets. Mesmo assim, os scores são 6,82 e 6,95. A contradição permanece com RZ total ou por jogo, com qualquer normalização individual monotônica comum e pesos não negativos. São dois TEs, então uma normalização comum por posição também não resolve esse par. Isso não identifica a regra ausente, mas impede atribuir o problema apenas à busca de pesos.

## Decisão

Não promover a candidata. O ajuste conjunto reduz parte do erro no novo recorte, mas piora o topo e transfere mal entre as capturas. Antes de ampliar novamente a busca de pesos, testar a presença de componentes adicionais já visíveis no relatório (por exemplo TDs e volume de produção), ou uma regra de normalização condicional. Nenhuma mudança no painel. Reprodução: `python scripts/research_trinity_normalization.py`, com as duas transcrições locais em `data/research/trinity_reference`.
