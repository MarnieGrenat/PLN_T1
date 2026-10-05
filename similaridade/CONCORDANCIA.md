# Concordância entre anotadores

Gerado por `similaridade/avaliar_concordancia.py`.

100 pares anotados por 2 alunos na escala Likert de 1 a 5. A nota final de cada par (`similaridade_media`) é a média das duas.

## Distribuição das notas

| nota | Gabriela (a1) | Renato (a2) |
|:-:|--:|--:|
| 1 | 93 | 68 |
| 2 | 5 | 4 |
| 3 | 2 | 5 |
| 4 | 0 | 16 |
| 5 | 0 | 7 |

Média das notas: Gabriela (a1) = 1.09, Renato (a2) = 1.90.

## Métricas

| métrica | valor |
|---|--:|
| concordância exata | 67% |
| diferença de até 1 ponto | 71% |
| diferença absoluta média | 0.87 |
| kappa de Cohen | 0.095 (leve) |
| kappa ponderado linear | 0.069 (leve) |
| kappa ponderado quadrático | 0.086 (leve) |
| correlação de Pearson | 0.242 |
| correlação de Spearman | 0.265 |

O kappa simples trata toda divergência como igual; os ponderados penalizam mais as divergências grandes (dar 1 e 5 pesa mais que 1 e 2), o que combina melhor com uma escala ordinal. Spearman mede se os dois ordenam os pares de forma parecida, mesmo que um use a escala de forma mais compressa que o outro. Interpretação do kappa: escala de Landis & Koch (1977).

## Maiores divergências

| par | Gabriela (a1) | Renato (a2) |
|---|:-:|:-:|
| código – proteção | 1 | 5 |
| domínio – infraestrutura | 1 | 5 |
| host – comando | 1 | 5 |
| ordem – gestão | 1 | 5 |
| entrada – tráfego | 1 | 4 |
| senha – vulnerabilidade | 1 | 4 |
| modelo – autenticação | 1 | 4 |
| base – gerar | 1 | 4 |
| ataque – dado | 1 | 4 |
| operar – administrador | 1 | 4 |

## Pares mais e menos similares (nota média)

Mais similares: exigir–requisito (4.0), comunicação–rede (3.5), computador–nuvem (3.5), código–proteção (3.0), domínio–infraestrutura (3.0), host–comando (3.0), realizar–atender (3.0), ordem–gestão (3.0)

Menos similares: análise–índice (1.0), integridade–incidente (1.0), arquivo–segurança (1.0), objeto–desenvolvimento (1.0), função–corporativo (1.0)
