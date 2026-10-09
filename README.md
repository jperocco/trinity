# Trinity — laboratório de usage WR/TE

Projeto independente do JJ Stats. Escopo inicial: WR e TE, temporada regular. Produto final: explorador interativo com score de papel ofensivo, filtros, eixos configuráveis e componentes transparentes. RB fora do escopo.

## Estado confirmado — 2026-10-09
- Repositório originalmente vazio; acesso de escrita confirmado.
- Especificação inicial e protocolo de validação definidos abaixo.
- Histórico público 2021–2025 baixado e auditado. Nenhum peso treinado; nenhum score validado.
- Pipeline canônico de auditoria/agregação implementado, com sete testes aprovados.
- Exportador semanal PFF preparado; detalhes em docs/ACQUISITION.md.
- Principal dependência: acesso aos CSVs PFF históricos e à exportação JJ Stats/PFF 2026, com denominador compatível.
- Próxima execução: auditar cobertura dos arquivos históricos de targets/air yards/PPR e selecionar fonte de rotas. Não publicar score com proxy de rotas.

## Sequência e entregáveis
1. Definição: medir participação e concentração do papel no jogo aéreo do próprio time.
2. Dados: inventário de fontes, licenças, cobertura por ano e campos; dataset player-game 2021–2025; 2026 separado como monitoramento.
3. Auditoria: duplicações, identidade, ausências, denominadores, mudanças de fornecedor e cobertura WR/TE.
4. Ingredientes: distribuição, estabilidade e ganho incremental de Route Share, Target Share e Air Yard Share.
5. Modelo: regressão regularizada interpretável; testar modelo conjunto e separado por posição. Pesos aprendidos só no treino.
6. Backtest: divisão temporal; comparar contra cada ingrediente, PPR/G anterior e combinação simples. STOP se não houver ganho útil fora da amostra.
7. Escala: transformação monotônica para 0–10, calibrada no treino; referências históricas por posição.
8. Explorer: score × PPR/G; filtros de time, jogador, posição, temporada, semanas e amostra; eixos substituíveis.
9. Drill-down: componentes, amostra, fonte, tendência e comparação; jogador fixado permanece destacado ao mudar filtros.
10. Integração: somente depois de dados auditados, modelo validado e Explorer funcional.

## Contrato do dataset v0.1
Unidade canônica: player_id + game_id + team. Agregar semanas e temporadas a partir desta base. Preservar stint de time em trades; posição e identidade verificadas no período.

| Campo | Regra |
|---|---|
| player_id, game_id, season, week, team, position | IDs estáveis; WR/TE; temporada regular |
| routes | Rotas efetivamente corridas; jamais inferir de snaps |
| team_route_opportunities | Oportunidades de passe elegíveis na mesma definição do fornecedor de routes |
| targets, team_targets | Targets atribuídos a jogadores; denominador inclui todas as posições |
| receiving_air_yards, team_receiving_air_yards | Mesma fonte e universo de targets; conservar valores negativos |
| fantasy_points_ppr | Full PPR; guardar convenção de pontuação, incluindo rushing e fumbles |
| offensive_snaps, team_offensive_snaps | Contexto opcional; não substituem routes |
| played, source, source_version, extracted_at | Participação, procedência e data; distinguir zero de missing |
| routes_source, routes_definition | Metadados específicos para compatibilidade histórica |

Route Share = soma(routes) / soma(team_route_opportunities).
Target Share = soma(targets) / soma(team_targets).
Air Yard Share = soma(receiving_air_yards) / soma(team_receiving_air_yards).
Não calcular média simples de shares semanais para intervalos.
Denominador zero gera missing. Air yards negativos ou share fora de 0–1 geram flag, não corte silencioso.
PPR/G usa jogos disputados verificados, inclusive jogos com zero targets; bye/inativo não vira zero.

Para o papel NFL, denominadores contam oportunidades do time nos jogos disputados pelo jogador. Mostrar separadamente disponibilidade e produção por semana de calendário. Não misturar estas definições no treinamento.

## Fontes e lacunas
- nflverse player stats / play-by-play: candidato para targets, air yards, pontos, contexto e IDs. Cobertura real 2021–2025 ainda precisa ser auditada nos arquivos.
- nflverse participation: útil para presença em campo e contexto. O campo route descreve a rota do recebedor principal do play, não routes run de todos os jogadores. Não resolve Route Share.
- Rotas históricas: PFF selecionado como fonte primária; extração real ainda depende de acesso/exportação. Exigir cobertura WR/TE, definição dos pass plays, jogos sem targets e permissão de uso no produto. Avaliar exportação licenciada ou dados existentes com procedência verificada; não presumir acesso pago.
- 2026: usar exportação JJ Stats, fonte primária PFF; cobertura e compatibilidade ainda precisam de auditoria.

Documentação consultada:
https://nflreadr.nflverse.com/reference/load_player_stats.html
https://nflreadr.nflverse.com/articles/dictionary_participation.html
https://nflreadr.nflverse.com/reference/load_participation.html

## Protocolo de validação
- Objetivo primário: últimas 3 semanas de jogos de equipe → próximas 3 semanas de equipe. Reportar produção por jogo disputado e por semana de equipe separadamente.
- Secundários: W1–4 → W5–8; primeira metade → segunda; temporada N → N+1.
- Não selecionar elegibilidade usando produção futura. Para testes com mínimo de jogos futuros, declarar viés de sobrevivência e reportar attrition.
- Amostra mínima e regularização selecionadas em folds internos temporais. Exibir sensibilidade a cortes de games/routes.
- Treino inicial em anos anteriores; validação walk-forward; reservar 2025 para teste final. Se tuning já usar 2025, ele deixa de ser holdout.
- Purga de janelas sobrepostas na fronteira treino/validação; imputação, normalização, pesos e escala ajustados apenas no treino.
- Comparações na mesma amostra: PPR/G passado; cada share isolado; Target Share + Air Yard Share; tríade.
- Métricas: MAE, RMSE, correlação Pearson/Spearman e ordenação por posição; intervalos de incerteza com reamostragem agrupada por jogador.
- Reportar ganho incremental de routes e air yards e consistência entre folds/posições. Correlação não é taxa de acerto.
- Separar papel e ambiente: mostrar passes/jogo e volume do ataque no contexto. Testar contribuição do ambiente separadamente.
- STOP: sem melhoria estável fora da amostra, não declarar validade preditiva nem inventar pesos/labels. Registrar resultado e reavaliar objetivo.

## Critério para sair da etapa de dados
Inventário versionado com cobertura por ano/posição; fonte de routes aceita; chaves reconciliadas; denominadores consistentes; auditoria de missing/zeros; licença registrada; amostra reprodutível calculada manualmente e pelo pipeline.
