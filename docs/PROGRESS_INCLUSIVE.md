# Progresso — importação inclusiva e preparo de backtest

Atualiza o estado de UPDATED_SNAPSHOT.md.

937/963 registros WR/TE elegíveis (97,3%). Dos 112 registros sem ID, todos têm targets=0: 87 têm PPR preenchido e foram preservados com IDs locais provisórios jj-local. Air yards de recebedor sem targets são zero por definição; denominador de equipe vem de peers consistentes no mesmo jogo. Não imputar PPR ausente. 26 excluídos, 2,7% do universo; investigação residual pausada por relevância.

IDs provisórios não são GSIS/PFF e não participam por padrão da preparação de treino. Não reconciliar só pelo nome com fontes externas. Usar relatório JJ_INCLUSIVE_AUDIT.json.

prepare_backtest.py produz janelas estritamente futuras, sem misturar trades e sem preencher bye/ausência com zero. Teste operacional 1 semana → próxima: 520 pares. Janela 3→3: zero pares com apenas W1–4; nenhum score treinado.

Limitação: a primeira versão usa semanas de calendário completas, não sequência de jogos da equipe. É experimento complete-case com viés de seleção, ainda não protocolo primário. Necessário calendário, ledger e histórico PFF antes de validar pesos. Nenhuma correlação preditiva divulgada.

16 testes passam, incluindo vazamento temporal, troca de time, ID provisório, falta de semana e ausência de imputação de PPR.

Dependência externa restante: CSV histórico PFF ou acesso autenticado autorizado. Exportador pronto; não há credencial PFF disponível. Nenhum pedido de compra ou login foi executado.
