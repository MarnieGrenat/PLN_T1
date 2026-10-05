# Similaridade de palavras: comparação dos modelos

Análise dos resultados de [`ANALISE_MODELOS.md`](ANALISE_MODELOS.md) (gerado por `avaliar_modelos.py`). Nota humana de
referência: média dos dois anotadores em `similaridade_final.csv` (100 pares do corpus próprio). Métrica: correlação de
Spearman, com intervalo de confiança de 95% por bootstrap.

> **Aviso:** o LLM avaliado é o Claude Sonnet 5.5, e esta análise foi escrita por ele. As notas do LLM foram dadas às cegas
> (só as palavras de cada par), mas quem lê deve ter isso em mente. Detalhes em
> [`resultados/LLM_CLAUDE.md`](resultados/LLM_CLAUDE.md).

## Resultados

| modelo | tipo | Spearman | IC 95% |
|---|---|--:|---|
| Claude Sonnet 5.5 (nota 1–5) | LLM | **0,545** | [0,38; 0,70] |
| spaCy `pt_core_news_lg` | estático | 0,173 | [0,01; 0,35] |
| `bert-base-uncased` (palavra em contexto) | transformer | −0,051 | [−0,26; 0,15] |
| `bert-base-uncased` (palavra isolada) | transformer | −0,036 | [−0,23; 0,15] |

**Referência humana.** Os dois anotadores têm Spearman 0,265 entre si. Como a nota de comparação é a média dos dois
(menos ruidosa que um anotador só), a fórmula de Spearman-Brown dá confiabilidade 0,42 e, portanto, um teto realista de
cerca de **0,65** para qualquer modelo. Em relação a esse teto, o Claude chega a uns 84%, o spaCy a uns 27% e o BERT a 0%.

## Leitura dos resultados

1. **O LLM é o melhor, com folga.** Seu intervalo de confiança ([0,38; 0,70]) mal encosta no do spaCy ([0,01; 0,35]), então
   a diferença é real, apesar da amostra pequena. Correlaciona de forma parecida com os dois anotadores (0,47 e 0,48), isto é,
   não está "copiando" o critério de só um deles.
2. **O modelo estático tem sinal fraco.** Os vetores do spaCy capturam sobretudo coocorrência/tema geral, o que dá
   cosseno alto para pares que os humanos acham sem relação (ex.: `informação`–`verificar`, `backup`–`usuário`, `integridade`–`incidente`).
   Curiosamente correlaciona mais com a Gabriela (0,34) do que com o Renato (0,12), o que reflete que os dois
   anotadores usaram a escala de formas diferentes.
3. **O `bert-base-uncased` não tem sinal (≈ 0).** Era esperado: o modelo é treinado só em inglês, e palavras do português viram
   pedaços de subpalavras sem relação com seu significado. Não é um resultado sobre "BERT" em geral e sim sobre
   usar um modelo monolíngue em inglês em outra língua. Usar contexto (média de até 20 ocorrências no corpus) não ajudou
   (−0,05 contra −0,04): o problema é o modelo, não a falta de contexto. O BERT em contexto e o isolado concordam entre si
   (0,56), mas nenhum dos dois concorda com os humanos.
4. **Os modelos quase não concordam entre si**, exceto spaCy–Claude (0,37) e as duas variantes do BERT (0,56). A discordância
   entre modelos é parte do problema: não há uma noção única de "similaridade" nos pares sorteados.
5. **Onde o LLM erra.** As maiores divergências são em pares abstratos que os humanos acharam moderadamente parecidos
   (nota 2,5) e o LLM acha sem relação (nota 1): `base`–`gerar`, `componente`–`acessar`, `modelo`–`autenticação`,
   `virtual`–`seguro`. Em sentido contrário, o LLM dá 2 para pares que ambos humanos deram 1 (`integridade`–`incidente`,
   `teste`–`ação`, `informação`–`verificar`): vê relação temática onde os humanos não viram.

## Limitações

- **Teto baixo e ruidoso.** Com concordância humana de 0,27, diferenças pequenas entre modelos não são interpretáveis; só as
  grandes (LLM contra os demais) são confiáveis.
- **100 pares, quase todos sem relação.** A maioria dos pares tem nota humana 1; há pouca variação para medir.
- **Falta o BERT em português.** O `bert-base-uncased` pedido no enunciado foi testado, mas o BERTimbau
  (`neuralmind/bert-base-portuguese-cased`) ainda não: precisa de GPU/Colab (`colab_modelos.ipynb`). É esperado que ele
  fique bem acima do BERT em inglês, e talvez perto do spaCy.
- **Dataset da aula.** Não temos o dataset de palavras feito em aula; `--dataset-aula` aceita o CSV e separa as métricas.
- **LLM não reprodutível por script.** As notas vieram de uma conversa, em uma passada. Uma versão por API
  (`--llm-backend anthropic`) ou com LLM aberto (`--llm-backend hf`) está pronta no `avaliar_modelos.py`.
- **Notas inteiras do LLM** geram muitos empates (54 pares com nota 1), o que limita o Spearman possível.
