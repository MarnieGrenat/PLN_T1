# Estatísticas do corpus

Gerado por `scraper/estatisticas_dataset.py` a partir de `dataset/questoes.jsonl`.

## Visão geral

| métrica | valor |
|---|---|
| questões | 274 |
| provas de origem | 13 |
| tokens (enunciado + alternativas) | 26345 |
| vocabulário (tipos distintos) | 4598 |
| palavras que aparecem 1 vez | 2232 |

## Questões por subárea e ano

| subárea | 2023 | 2024 | 2025 | 2026 | total | provas |
|---|---|---|---|---|---|---|
| redes | – | 69 | – | – | 69 | 2 |
| seguranca | 25 | 75 | 7 | 28 | 135 | 8 |
| sistemas | 28 | 17 | – | 25 | 70 | 3 |
| **total** | 53 | 161 | 7 | 53 | 274 | 13 |

## Tamanho dos textos (em tokens)

Células: média / mediana / mín / máx.

| subárea | enunciado | alternativa (cada) | questão inteira |
|---|---|---|---|
| redes | 42.4 / 38 / 20 / 85 | 10.7 / 7 / 1 / 45 | 85.1 / 81 / 30 / 197 |
| seguranca | 54.2 / 39 / 9 / 244 | 8.3 / 4 / 0 / 140 | 92.7 / 81 / 17 / 270 |
| sistemas | 74.6 / 59 / 14 / 437 | 8.2 / 4 / 1 / 111 | 113.8 / 95 / 28 / 564 |
| todas | 56.5 / 44 / 9 / 437 | 8.8 / 4 / 0 / 140 | 96.1 / 86 / 17 / 564 |

## Alternativas e gabarito

Número de alternativas: 4 → 134, 5 → 140

Distribuição da letra correta:

| subárea | A | B | C | D | E |
|---|---|---|---|---|---|
| redes | 17 (25%) | 20 (29%) | 16 (23%) | 16 (23%) | 0 (0%) |
| seguranca | 33 (24%) | 30 (22%) | 34 (25%) | 24 (18%) | 14 (10%) |
| sistemas | 15 (21%) | 15 (21%) | 14 (20%) | 18 (26%) | 8 (11%) |
| todas | 65 (24%) | 65 (24%) | 64 (23%) | 58 (21%) | 22 (8%) |

## Palavras mais frequentes por subárea

Sem stopwords; acentos preservados na exibição. Top 15.

- **redes**: rede (76), dados (40), segurança (34), redes (33), sistema (30), recursos (26), acesso (26), dispositivos (20), sistemas (19), virtuais (19), máquina (18), cabeamento (18), protocolo (17), servidores (16), enquanto (16)
- **seguranca**: dados (69), segurança (67), rede (59), informação (48), tipo (42), acesso (40), sistema (39), iii (34), uso (31), protocolo (30), serviços (29), aplicação (26), redes (25), autenticação (25), servidor (24)
- **sistemas**: dados (63), sistema (38), código (31), div (28), tipo (28), iii (26), página (20), forma (19), uso (19), execução (17), software (17), html (16), http (16), desenvolvimento (15), padrão (15)

## Palavras características de cada subárea

Maior razão entre a frequência relativa na subárea e no resto do corpus (mínimo de 5 ocorrências na subárea).

- **redes**: cabeamento (18), fibra (11), samba (10), máquina (18), associação (7), máscara (13), vmware (6), cobre (6), distâncias (5), óptica (5), cabos (5), vsphere (5)
- **seguranca**: ataque (18), risco (15), diferencial (12), incremental (12), pessoais (11), lgpd (11), raid (10), ipv6 (18), técnico (9), request (8), controles (8), público (8)
- **sistemas**: class (13), pessoa (11), trecho (9), body (9), anotação (9), pedidos (9), select (9), html (16), spring (8), apis (8), resultado (7), from (7)
