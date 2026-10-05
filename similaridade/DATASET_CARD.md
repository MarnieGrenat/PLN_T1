# Dataset Card — Similaridade de palavras (TI: redes, segurança e sistemas), versão 2

100 pares de palavras do vocabulário de TI em português, cada um com nota de similaridade em escala
Likert de 1 a 5, dada de forma independente por dois anotadores. Arquivo principal:
[`similaridade_final.csv`](similaridade_final.csv). Construído para o Trabalho 1 de PLN (PUCRS), a partir
do [corpus de questões de concursos](../dataset/README.md) (1500 questões). A versão 1, feita sobre um
corpus menor (274 questões), está arquivada em [`v1/`](v1/).

## Conteúdo

| arquivo | descrição |
|---|---|
| `similaridade_final.csv` | **resultado**: 100 pares com as notas dos dois anotadores e a média |
| `palavras_top200.csv` | os 200 lemas de origem: `rank, lema, frequencia, textos` |
| `pares_gabriela.csv`, `pares_renato.csv` | anotações originais de cada aluno (com nome e escala no topo) |
| `CONCORDANCIA.md` | métricas de concordância entre os anotadores |
| `construir_pares.py`, `avaliar_concordancia.py` | scripts que geram palavras/pares e o CSV final |

## Esquema de `similaridade_final.csv`

CSV UTF-8, separado por vírgula, com cabeçalho, 100 linhas de dados.

| coluna | tipo | descrição |
|---|---|---|
| `palavra_1` | texto | primeiro lema do par |
| `palavra_2` | texto | segundo lema do par |
| `similaridade_a1` | inteiro 1–5 | nota do anotador 1 (Gabriela Dellamora) |
| `similaridade_a2` | inteiro 1–5 | nota do anotador 2 (Renato Trindade) |
| `similaridade_media` | decimal | média das duas notas (de 1.0 a 5.0, em passos de 0.5) |

Exemplo:

```
palavra_1,palavra_2,similaridade_a1,similaridade_a2,similaridade_media
análise,índice,1,1,1.0
solução,problema,1,2,1.5
```

A ordem das palavras dentro do par não tem significado (a similaridade é tratada como simétrica).

## Escala Likert

| nota | significado |
|:-:|---|
| 1 | Totalmente dissimilar (ou Muito diferente) |
| 2 | Parcialmente dissimilar (ou Um pouco diferente) |
| 3 | Neutro / Indiferente (Nem similar, nem dissimilar) |
| 4 | Parcialmente similar (ou Um pouco parecido) |
| 5 | Totalmente similar (ou Muito parecido) |

## Como foi construído

1. **Texto de origem**: enunciados e alternativas das 1500 questões de `dataset/questoes.jsonl`
   (500 por subárea). Nos itens certo/errado só o enunciado entra, pois as "alternativas" são apenas
   Certo/Errado.
2. **Pré-processamento** (spaCy `pt_core_news_lg`): tokenização, lematização e remoção de stopwords.
   Ficam só substantivos, verbos e adjetivos, com lema alfabético de 3 letras ou mais, sem numerais
   romanos, nomes próprios/siglas, nem vocabulário de enunciado de prova ("assinalar", "alternativa",
   "julgue", "asserção").
3. **200 palavras mais representativas**: os lemas mais frequentes do corpus (de `dado`, 809
   ocorrências em 598 textos, até `eficiente`, 49 ocorrências em 48 textos); empate resolvido pelo
   número de textos em que o lema aparece.
4. **100 pares**: os 200 lemas foram embaralhados (semente 42) e emparelhados em sequência. Os pares são
   disjuntos: cada palavra aparece em exatamente um par.
5. **Anotação**: dois alunos anotaram os 100 pares de forma independente, cada um no seu arquivo, sem ver
   as respostas do outro.
6. **Consolidação**: `avaliar_concordancia.py` une as duas anotações e calcula a média por par.

## Estatísticas

Notas médias (`similaridade_media`): média 1.50, mediana 1, desvio-padrão 0.77, mínimo 1 e máximo 4.

| média do par | 1 | 1.5 | 2 | 2.5 | 3 | 3.5 | 4 |
|---|--:|--:|--:|--:|--:|--:|--:|
| pares | 66 | 4 | 7 | 15 | 5 | 2 | 1 |

Notas individuais:

| nota | Gabriela (a1) | Renato (a2) |
|:-:|--:|--:|
| 1 | 93 | 68 |
| 2 | 5 | 4 |
| 3 | 2 | 5 |
| 4 | 0 | 16 |
| 5 | 0 | 7 |

Concordância entre os anotadores (detalhes e interpretação em [`CONCORDANCIA.md`](CONCORDANCIA.md)):

| métrica | valor |
|---|--:|
| concordância exata | 67% |
| diferença de até 1 ponto | 71% |
| kappa de Cohen | 0.095 (leve) |
| kappa ponderado linear | 0.069 (leve) |
| kappa ponderado quadrático | 0.086 (leve) |
| correlação de Spearman | 0.265 |

## Limitações e usos adequados

- **Concordância baixa.** O kappa simples é de 0.095 e as correlações ficam em torno de 0,25. A
  concordância exata de 67% é inflada pelo desbalanceamento: 93% das notas de Gabriela são 1, e quando
  quase tudo é 1 concordar por acaso é fácil. Os dois anotadores usaram a escala de formas diferentes
  (Gabriela quase só nota 1, Renato usou também 4 e 5). A média atenua esse viés, mas não o elimina; para
  análises cuidadosas use também as colunas por anotador.
- **Muito desbalanceado.** 70 pares têm média abaixo de 2 e 8 chegam a 3 ou mais, pois pares sorteados ao acaso quase
  nunca são relacionados. Poucos exemplos de alta similaridade: o conjunto serve para uma avaliação
  preliminar e não separa bem níveis altos.
- **Só 2 anotadores e 100 pares**, ambos alunos da disciplina, não especialistas. A amostra é pequena
  para estimar correlações com intervalos de confiança estreitos.
- **Vocabulário de domínio e de um corpus de questões de concursos.** Inclui verbos e adjetivos genéricos
  (`permitir`, `definir`, `adequado`) além de termos técnicos (`protocolo`, `roteador`). Lematização
  automática: pode haver lemas incorretos.
- **Similaridade vs. relação.** As instruções não distinguem sinonímia de associação; as notas refletem a
  impressão geral de cada anotador.
- Uso previsto: avaliar vetores de palavras (por exemplo, correlação de Spearman entre a similaridade de
  cosseno e `similaridade_media`) em um domínio específico. Não é um benchmark geral de similaridade.
