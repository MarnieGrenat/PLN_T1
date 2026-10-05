# Notas do LLM (Claude Sonnet 5.5)

Arquivo de previsões: [`pred_llm-claude-sonnet-5-5.csv`](pred_llm-claude-sonnet-5-5.csv).

## Como foram geradas

- **Modelo:** Claude Sonnet 5.5, usado em uma conversa (sem chamada de API por script).
- **Entrada:** só as duas palavras de cada um dos 100 pares, na ordem do `similaridade_final.csv`. O modelo **não viu**
  as notas dos anotadores, as de outros modelos nem as colunas de nota do CSV.
- **Tarefa:** a mesma escala Likert dos anotadores (1 = totalmente dissimilar ... 5 = totalmente similar), julgando a
  similaridade semântica no vocabulário de TI (redes, segurança e sistemas).
- **Uma passada, sem revisão:** cada par recebeu uma nota inteira; não houve segunda rodada nem ajuste depois de ver os
  resultados.
- **Distribuição das notas:** 1 → 54, 2 → 32, 3 → 11, 4 → 3, 5 → 0.

## Limitações

- Não é reprodutível por script: o mesmo modelo pode dar notas ligeiramente diferentes em outra conversa. Para uma
  versão automatizada, `avaliar_modelos.py --modelos llm --llm-backend anthropic` usa o mesmo enunciado da escala via API.
- Notas inteiras geram muitos empates, o que limita a correlação de Spearman possível.
- Os pares vieram do mesmo corpus que o modelo "conhece" em geral (vocabulário de TI), então não há como separar
  conhecimento de domínio de simples leitura semântica das palavras.
