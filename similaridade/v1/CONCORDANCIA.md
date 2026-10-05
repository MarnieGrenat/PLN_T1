# Concordância entre anotadores

Gerado por `similaridade/avaliar_concordancia.py`.

100 pares anotados por 2 alunos na escala Likert de 1 a 5. A nota final de cada par (`similaridade_media`) é a média das duas.

## Distribuição das notas

| nota | anotador 1 | anotador 2 |
|:-:|--:|--:|
| 1 | 80 | 50 |
| 2 | 12 | 22 |
| 3 | 5 | 15 |
| 4 | 3 | 10 |
| 5 | 0 | 3 |

Média das notas: anotador 1 = 1.31, anotador 2 = 1.94.

## Métricas

| métrica | valor |
|---|--:|
| concordância exata | 52% |
| diferença de até 1 ponto | 79% |
| diferença absoluta média | 0.73 |
| kappa de Cohen | 0.148 (leve) |
| kappa ponderado linear | 0.268 (razoável) |
| kappa ponderado quadrático | 0.406 (moderada) |
| correlação de Pearson | 0.556 |
| correlação de Spearman | 0.483 |

O kappa simples trata toda divergência como igual; os ponderados penalizam mais as divergências grandes (dar 1 e 5 pesa mais que 1 e 2), o que combina melhor com uma escala ordinal. Spearman mede se os dois ordenam os pares de forma parecida, mesmo que um use a escala de forma mais compressa que o outro. Interpretação do kappa: escala de Landis & Koch (1977).

## Maiores divergências

| par | anotador 1 | anotador 2 |
|---|:-:|:-:|
| máquina – implementação | 1 | 4 |
| configurar – infraestrutura | 1 | 4 |
| disponibilidade – tecnologia | 1 | 4 |
| informação – proteção | 1 | 4 |
| uso – risco | 1 | 3 |
| organização – privado | 1 | 3 |
| usuário – web | 2 | 4 |
| classe – computacional | 1 | 3 |
| permissão – ambiente | 1 | 3 |
| responsável – equipe | 2 | 4 |

## Pares mais e menos similares (nota média)

Mais similares: senha–criptografar (4.5), comando–controle (4.5), programa–computador (4.0), desenvolvimento–teste (3.5), funcionalidade–aplicativo (3.5), software–pacote (3.5), usuário–web (3.0), responsável–equipe (3.0)

Menos similares: aplicar–disco (1.0), específico–falha (1.0), algoritmo–atributo (1.0), porta–manter (1.0), ataque–armazenamento (1.0)
