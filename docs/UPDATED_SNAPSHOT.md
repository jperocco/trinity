# Banco atualizado recebido em 2026-10-09

64 jogos FINAL, Weeks 1–4. 963 registros WR/TE; 962 com rotas PFF não estimadas.

Importação estrita: 639 registros completos W1–3. A W4 tem air_yards_share e receiving_air_yards, mas não team_air_yards persistido.

Recuperação opcional: divisão de air yards do jogador pelo share arquivado. Exigir ao menos dois registros não-zero por time-jogo, denominador positivo inteiro e concordância absoluta <1e-6. Conferir cada share importado com tolerância <1e-8. Sem média, clipping ou imputação de zeros.

Com recuperação: 850 registros W1–4 (215, 208, 216, 211). 113 excluídos, principalmente sem IDs/air yards de jogador. A concordância prova consistência interna, não validação externa. Origem da recuperação gravada por linha. Relatório JJ_UPDATED_AUDIT.json.

Não alterar banco original. Não substituir a amostra estrita nem treinar score nesta etapa. Dados reais derivados ficam locais; repositório público recebe código e contagens.

```bash
python scripts/import_jj.py /caminho/jj_stats.sqlite --recover-air-denominators --output data/raw/jj/canonical_recovered_2026.csv --report docs/JJ_UPDATED_AUDIT.json
```

O relatório anterior documenta o snapshot antigo. Este documento é o estado mais recente.
