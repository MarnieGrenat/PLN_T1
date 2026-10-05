# Dataset Card — Similaridade de palavras (TI: redes, segurança e sistemas)

100 pares de palavras do vocabulário de TI em português, cada um com nota de similaridade em escala
Likert de 1 a 5, dada de forma independente por dois anotadores. Arquivo principal:
[`similaridade_final.csv`](similaridade_final.csv). Construído para o Trabalho 1 de PLN (PUCRS), a partir
do [corpus de questões de concursos](../dataset/README.md).

## Conteúdo

| arquivo | descrição |
|---|---|
| `similaridade_final.csv` | **resultado**: 100 pares com as notas dos dois anotadores e a média |
| `palavras_top200.csv` | os 200 lemas de origem: `rank, lema, frequencia, textos` |
| `pares_anotador1.csv`, `pares_anotador2.csv` | anotações originais de cada aluno (com cabeçalho de nome e escala) |
| `CONCORDANCIA.md` | métricas de concordância entre os anotadores |
| `construir_pares.py`, `avaliar_concordancia.py` | scripts que geram palavras/pares e o CSV final |

## Esquema de `similaridade_final.csv`

CSV UTF-8, separado por vírgula, com cabeçalho, 100 linhas de dados.

| coluna | tipo | descrição |
|---|---|---|
| `palavra_1` | texto | primeiro lema do par |
| `palavra_2` | texto | segundo lema do par |
| `similaridade_a1` | inteiro 1–5 | nota do anotador 1 |
| `similaridade_a2` | inteiro 1–5 | nota do anotador 2 |
| `similaridade_media` | decimal | média das duas notas (de 1.0 a 5.0, em passos de 0.5) |

Exemplo:

```
palavra_1,palavra_2,similaridade_a1,similaridade_a2,similaridade_media
aplicar,disco,1,1,1.0
desenvolvimento,teste,3,4,3.5
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

1. **Texto de origem**: enunciados e alternativas das 274 questões da primeira versão de
   `dataset/questoes.jsonl`. O corpus de questões foi ampliado depois (veja `dataset/README.md`); as
   palavras e os pares **não foram regerados**, para não invalidar as anotações já feitas.
2. **Pré-processamento** (spaCy `pt_core_news_lg`): tokenização, lematização e remoção de stopwords.
   Ficam só substantivos, verbos e adjetivos, com lema alfabético de 3 letras ou mais, sem numerais
   romanos, nomes próprios/siglas, nem vocabulário de enunciado de prova ("assinalar", "alternativa").
3. **200 palavras mais representativas**: os lemas mais frequentes do corpus (de `rede`, 188
   ocorrências em 126 questões, até `tarefa`, 11 ocorrências em 9 questões); empate resolvido pelo número
   de questões em que o lema aparece.
4. **100 pares**: os 200 lemas foram embaralhados (semente 42) e emparelhados em sequência. Os pares são
   disjuntos: cada palavra aparece em exatamente um par.
5. **Anotação**: dois alunos anotaram os 100 pares de forma independente, cada um no seu arquivo, sem ver
   as respostas do outro.
6. **Consolidação**: `avaliar_concordancia.py` une as duas anotações e calcula a média por par.

## Estatísticas

Notas médias (`similaridade_media`): média 1,62, mediana 1,5, desvio-padrão 0,82, mínimo 1,0 e máximo 4,5.

| média do par | 1,0 | 1,5 | 2,0 | 2,5 | 3,0 | 3,5 | 4,0 | 4,5 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|
| pares | 48 | 18 | 16 | 8 | 4 | 3 | 1 | 2 |

Notas individuais:

| nota | anotador 1 | anotador 2 |
|:-:|--:|--:|
| 1 | 80 | 50 |
| 2 | 12 | 22 |
| 3 | 5 | 15 |
| 4 | 3 | 10 |
| 5 | 0 | 3 |

Concordância entre os anotadores (detalhes e interpretação em [`CONCORDANCIA.md`](CONCORDANCIA.md)):

| métrica | valor |
|---|--:|
| concordância exata | 52% |
| diferença de até 1 ponto | 79% |
| kappa de Cohen | 0,148 |
| kappa ponderado linear | 0,268 |
| kappa ponderado quadrático | 0,406 |
| correlação de Spearman | 0,483 |

## Limitações e usos adequados

- **Muito desbalanceado.** 66% dos pares têm média abaixo de 2 e só 10% chegam a 3 ou mais, pois pares
  sorteados ao acaso quase nunca são relacionados. Poucos exemplos de alta similaridade (3 pares com média
  de 4 ou mais): o conjunto serve para uma avaliação preliminar e não separa bem níveis de similaridade
  altos.
- **Concordância baixa a moderada** (kappa simples 0,15; ponderado quadrático 0,41). O anotador 1 usou
  a escala de forma mais compressa (80% de notas 1) que o anotador 2. A média das notas atenua o viés
  individual, mas não o elimina; para análises mais cuidadosas use também as colunas por anotador.
- **Só 2 anotadores e 100 pares**, ambos alunos da disciplina, não especialistas. A amostra é pequena
  para estimar correlações com intervalos de confiança estreitos.
- **Vocabulário de domínio e de um corpus pequeno.** As palavras vêm de questões de poucos concursos
  (13 provas) e incluem verbos e adjetivos genéricos (`permitir`, `definir`, `adequado`) além de termos
  técnicos (`protocolo`, `roteador`). Lematização automática: pode haver lemas incorretos.
- **Similaridade vs. relação.** As instruções não distinguem sinonímia de associação (como `senha` e
  `criptografar`); as notas refletem a impressão geral de cada anotador.
- Uso previsto: avaliar vetores de palavras (por exemplo, correlação de Spearman entre a similaridade de
  cosseno e `similaridade_media`) em um domínio específico. Não é um benchmark geral de similaridade.
