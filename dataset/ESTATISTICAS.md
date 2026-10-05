# Estatísticas do corpus

Gerado por `scraper/estatisticas_dataset.py` a partir de `dataset/questoes.jsonl`.

## Visão geral

| métrica | valor |
|---|---|
| questões | 1500 |
| provas de origem | 77 |
| tokens (enunciado + alternativas) | 127442 |
| vocabulário (tipos distintos) | 10902 |
| palavras que aparecem 1 vez | 4690 |

## Questões por subárea e ano

| subárea | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 | total | provas |
|---|---|---|---|---|---|---|---|---|---|
| redes | – | – | – | – | 312 | 70 | 118 | 500 | 23 |
| seguranca | 34 | 14 | 36 | 104 | 191 | 105 | 16 | 500 | 29 |
| sistemas | – | – | – | 21 | 39 | 274 | 166 | 500 | 25 |
| **total** | 34 | 14 | 36 | 125 | 542 | 449 | 300 | 1500 | 77 |

## Tamanho dos textos (em tokens)

Células: média / mediana / mín / máx.

| subárea | enunciado | alternativa (cada) | questão inteira |
|---|---|---|---|
| redes | 51.4 / 33 / 9 / 365 | 9.4 / 4 / 1 / 103 | 88.9 / 69 / 13 / 547 |
| seguranca | 50.4 / 39 / 3 / 200 | 6.5 / 3 / 1 / 140 | 74.7 / 56 / 12 / 380 |
| sistemas | 56.9 / 46 / 7 / 437 | 7.5 / 4 / 0 / 111 | 91.3 / 87 / 13 / 564 |
| todas | 52.9 / 39 / 3 / 437 | 7.8 / 4 / 0 / 140 | 85.0 / 71 / 12 / 564 |

## Alternativas e gabarito

Número de alternativas: 2 → 347, 4 → 307, 5 → 846

Distribuição da letra correta:

| subárea | A | B | C | D | E |
|---|---|---|---|---|---|
| redes | 72 (14%) | 87 (17%) | 156 (31%) | 81 (16%) | 104 (21%) |
| seguranca | 49 (10%) | 77 (15%) | 165 (33%) | 76 (15%) | 133 (27%) |
| sistemas | 91 (18%) | 106 (21%) | 130 (26%) | 90 (18%) | 83 (17%) |
| todas | 212 (14%) | 270 (18%) | 451 (30%) | 247 (16%) | 320 (21%) |

## Palavras mais frequentes por subárea

Sem stopwords; acentos preservados na exibição. Top 15.

- **redes**: rede (349), dados (204), sistema (163), iii (159), acesso (135), certo (128), errado (128), segurança (114), redes (111), protocolo (110), sistemas (102), camada (101), servidor (94), cada (84), criptografia (84)
- **seguranca**: segurança (256), dados (223), certo (180), errado (179), rede (150), informação (142), sistema (124), acesso (96), servidor (82), tipo (80), riscos (76), autenticação (73), gestão (70), iii (68), usuário (68)
- **sistemas**: dados (411), iii (192), sistema (185), software (113), sistemas (112), desenvolvimento (104), valor (94), código (89), forma (87), segurança (82), banco (80), analise (78), execução (78), rede (72), modelo (71)

## Palavras características de cada subárea

Maior razão entre a frequência relativa na subárea e no resto do corpus (mínimo de 5 ocorrências na subárea).

- **redes**: cabeamento (30), docente (24), formação (20), aprendizagem (16), samba (14), jitter (13), curricular (13), gbps (12), baterias (11), autonomia (10), marque (10), estudantes (20)
- **seguranca**: challenge (9), consequências (8), crime (8), injection (15), abc123 (7), carlos (7), etir (7), invasão (7), requerer (7), solicitou (7), crédito (12), ameaça (6)
- **sistemas**: cref2 (18), índice (34), class (15), classe (57), escreva (14), java (27), subárea (13), classes (37), scrum (46), acoplamento (11), subclasse (11), id_cliente (10)
