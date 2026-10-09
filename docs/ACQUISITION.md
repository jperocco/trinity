# Aquisição — estado 2026-10-09

## PFF: fonte primária de rotas
2026: exportação do JJ Stats com procedência PFF. Nenhuma alteração no JJ; trazer cópia com routes e denominador, IDs, semana e definição.
2021–2025: Premium Stats receiving, exportação por semana. O PFF documenta export CSV na interface e via CLI/API. API exige PFF Pro; não há credencial ou exportação PFF disponível neste checkout. Não confundir assinatura Premium Stats com acesso automático à API.

O script abaixo imprime o plano; só executa com --execute, Restish instalado e sessão autorizada já configurada:

```bash
python scripts/export_pff.py --seasons 2021 2022 2023 2024 2025
python scripts/export_pff.py --seasons 2025 --weeks 1 --execute
```

Antes de executar todas as semanas, inspecionar um CSV real: confirmar campo routes, cobertura inclusive zero targets, IDs PFF, time e definição. Consultar relatório de passing do time para o denominador; não somar rotas de recebedores para inventar dropbacks. O adapter PFF → contrato canônico só será mapeado após verificar cabeçalhos reais. Preservar ID PFF separado do GSIS; reconciliação explícita, nunca apenas nome.

Referências primárias:
- https://developer.pff.com/guide/querying/
- https://developer.pff.com/guide/exporting/
- https://profootballfocussupport.zendesk.com/hc/en-us/articles/32094827302163-Does-API-access-come-with-a-subscription

## nflverse
Targets, air yards e PPR: candidato público complementar. Verificar schema vigente e licença de cada dataset. Denominadores do time incluem RB/QB/outros, mesmo com output WR/TE.
Assets históricos 2021–2024 baixados e auditados. O endpoint legado de 2025 retornou 404; código oficial do nflreadr aponta o novo endpoint stats_player/stats_player_week_2025.csv. Resultado de cobertura e checksums em NFLVERSE_AUDIT.json. Dados brutos locais ignorados pelo git; ledger de participação e routes ainda ausentes.

## Pipeline disponível
CSV canônico com os campos do README:
```bash
python trinity.py data/raw/canonical.csv --start-week 1 --end-week 4 --output data/processed/w1-w4.json
python -m unittest discover -s tests -v
```
O pipeline bloqueia erros e conserva flags de air yards. Não gera score: faltam dados reais para treino e backtest.
Arquivos brutos, bancos e credenciais ficam fora do git.
