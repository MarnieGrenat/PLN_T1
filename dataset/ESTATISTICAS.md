# Estatísticas do corpus

Gerado por `scraper/estatisticas_dataset.py` a partir de `dataset/questoes.jsonl`.

## Visão geral

| métrica | valor |
|---|---|
| questões | 1987 |
| provas de origem | 78 |
| tokens (enunciado + alternativas) | 168387 |
| vocabulário (tipos distintos) | 12407 |
| palavras que aparecem 1 vez | 5163 |

## Questões por subárea e ano

| subárea | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 | total | provas |
|---|---|---|---|---|---|---|---|---|---|
| redes | – | – | – | – | 424 | 90 | 155 | 669 | 24 |
| seguranca | 57 | 23 | 51 | 151 | 275 | 169 | 28 | 754 | 29 |
| sistemas | – | – | – | 28 | 42 | 301 | 193 | 564 | 25 |
| **total** | 57 | 23 | 51 | 179 | 741 | 560 | 376 | 1987 | 78 |

## Tamanho dos textos (em tokens)

Células: média / mediana / mín / máx.

| subárea | enunciado | alternativa (cada) | questão inteira |
|---|---|---|---|
| redes | 51.2 / 33 / 9 / 365 | 9.4 / 4 / 1 / 103 | 88.4 / 69 / 13 / 547 |
| seguranca | 50.9 / 39 / 3 / 244 | 6.5 / 3 / 1 / 140 | 75.4 / 57 / 12 / 380 |
| sistemas | 57.5 / 46 / 7 / 437 | 7.7 / 4 / 0 / 111 | 93.0 / 88 / 13 / 564 |
| todas | 52.9 / 39 / 3 / 437 | 7.8 / 4 / 0 / 140 | 84.7 / 71 / 12 / 564 |

## Alternativas e gabarito

Número de alternativas: 2 → 485, 4 → 392, 5 → 1110

Distribuição da letra correta:

| subárea | A | B | C | D | E |
|---|---|---|---|---|---|
| redes | 98 (15%) | 116 (17%) | 211 (32%) | 104 (16%) | 140 (21%) |
| seguranca | 89 (12%) | 109 (14%) | 244 (32%) | 104 (14%) | 208 (28%) |
| sistemas | 105 (19%) | 119 (21%) | 140 (25%) | 107 (19%) | 93 (16%) |
| todas | 292 (15%) | 344 (17%) | 595 (30%) | 315 (16%) | 441 (22%) |

## Palavras mais frequentes por subárea

Sem stopwords; acentos preservados na exibição. Top 15.

- **redes**: rede (456), dados (288), sistema (223), iii (213), certo (181), errado (181), acesso (175), servidor (170), redes (151), segurança (148), protocolo (146), camada (136), sistemas (126), cada (125), servidores (108)
- **seguranca**: segurança (375), dados (335), certo (265), errado (264), rede (246), informação (214), sistema (185), acesso (158), tipo (127), riscos (118), servidor (117), sistemas (115), iii (112), criptografia (107), gestão (105)
- **sistemas**: dados (450), iii (215), sistema (210), software (135), sistemas (130), desenvolvimento (114), forma (107), código (99), valor (99), banco (97), execução (89), segurança (87), analise (87), modelo (86), cada (84)

## Palavras características de cada subárea

Maior razão entre a frequência relativa na subárea e no resto do corpus (mínimo de 5 ocorrências na subárea).

- **redes**: docente (41), formação (22), aprendizagem (21), samba (14), curricular (14), graduação (12), pedagógico (12), ensino (45), baterias (11), pedagógica (11), cursos (11), estudantes (22)
- **seguranca**: crime (13), intrusion (11), cibernética (11), consequências (10), challenge (9), tjrj (9), contratou (8), consultoria (8), íris (8), etir (8), risco (64), sede (7)
- **sistemas**: java (38), cref2 (18), class (17), coesão (14), subárea (14), escreva (14), scrum (51), spring (12), body (11), subclasse (11), polimorfismo (10), id_cliente (10)
