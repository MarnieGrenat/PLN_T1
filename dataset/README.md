# Dataset Card — Questões de concursos de TI (redes, segurança, sistemas)

Questões objetivas de **conhecimentos específicos** de concursos públicos brasileiros da área de TI,
coletadas do [PCI Concursos](https://www.pciconcursos.com.br) para o Trabalho 1 de PLN (PUCRS).
Cada questão traz enunciado, alternativas e gabarito, e está classificada por subárea e ano.

## Conteúdo

```
dataset/
├── raw.zip         352 .txt compactados (saída de `pdftotext -layout`): provas e gabaritos, um por PDF
├── redes/          <ano>.jsonl
├── seguranca/      <ano>.jsonl
├── sistemas/       <ano>.jsonl
├── questoes.jsonl  todas as questões em um único arquivo
└── descartes.csv   questões/provas descartadas e o motivo
```

Os arquivos dentro de `raw.zip` se chamam `<pasta-da-prova>__<nome-do-pdf>.txt`; o prefixo evita colisão entre
arquivos homônimos (`gabarito.txt`) de provas diferentes.

## Esquema (um objeto JSON por linha)

| campo          | descrição                                                                   |
|----------------|-----------------------------------------------------------------------------|
| `id`           | `<prova>#<número da questão>`                                               |
| `subarea`      | `redes`, `seguranca` ou `sistemas`                                          |
| `ano`          | ano da prova                                                                |
| `prova`        | identificador (slug) da prova no PCI Concursos                              |
| `numero`       | número da questão na prova                                                  |
| `tipo`         | `multipla_escolha` ou `certo_errado`                                        |
| `enunciado`    | texto do enunciado, sem as alternativas                                     |
| `alternativas` | objeto letra → texto (`{"A": "..."}`): 4 ou 5 alternativas; `{"C": "Certo", "E": "Errado"}` nos itens certo/errado |
| `gabarito`     | letra da alternativa correta                                                |

## Estatísticas

1500 questões (**500 por subárea**), vindas de 77 provas. Estatísticas completas do corpus (tokens,
vocabulário, tamanho dos textos, distribuição do gabarito, palavras mais frequentes e características por
subárea) em [`ESTATISTICAS.md`](ESTATISTICAS.md), geradas por `scraper/estatisticas_dataset.py`.

| subárea   | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 | total | provas |
|-----------|--:|--:|--:|--:|--:|--:|--:|------:|-------:|
| redes     | – | – | – | – | 312 | 70 | 118 | 500 | 23 |
| seguranca | 34 | 14 | 36 | 104 | 191 | 105 | 16 | 500 | 29 |
| sistemas  | – | – | – | 21 | 39 | 274 | 166 | 500 | 25 |

Por tipo de questão:

| subárea   | múltipla escolha | certo/errado | total |
|-----------|--:|--:|--:|
| redes     | 372 | 128 | 500 |
| seguranca | 321 | 179 | 500 |
| sistemas  | 460 | 40 | 500 |

846 questões têm 5 alternativas, 307 têm 4 e 347 são de certo/errado (Cebraspe; as "alternativas" são
`C` = Certo e `E` = Errado).

**Limite de 500 por subárea.** O processamento encontrou mais questões válidas (754 em seguranca, 564 em
sistemas, 669 em redes), mas o trabalho pede 500 por subárea. Foi sorteada uma amostra de 500 por subárea
(semente 42, reprodutível; ver `LIMITE_POR_SUBAREA` em `scraper/processar_dataset.py`). O excedente fica
registrado em `descartes.csv` com o motivo "excedente".

## Como foi construído

1. **Coleta**: `scraper/scraper_pci.py` baixa provas e gabaritos (PDF) das listagens de cada subárea.
2. **Texto**: `pdftotext -layout` em todos os PDFs → `raw.zip`.
3. **Processamento**: `scraper/processar_dataset.py`:
   - separa as colunas de cada página (o `-layout` intercala provas em duas colunas);
   - remove cabeçalhos, rodapés e marcas do site;
   - recorta a seção de conhecimentos específicos;
   - segmenta as questões e separa enunciado de alternativas;
   - junta o gabarito pelo número da questão. Em gabaritos com vários cargos, escolhe o bloco do cargo
     da prova pelo nome (e pelo número do cargo, no Cebraspe); se não houver um único melhor, descarta.

Para regenerar: `python3 scraper/processar_dataset.py` (lê `dataset/raw.zip`, grava em `dataset/`).

## Filtros (ver `descartes.csv`)

Descartadas: gabarito que não corresponde à prova (cobertura < 60% dos números de questão ou uma letra
dominando > 70% das respostas), conteúdo fora do domínio (orçamento público, que vem junto da parte
específica de alguns concursos), caracteres corrompidos pela conversão, questões sem alternativas identificáveis, sem
resposta no gabarito, anuladas, duplicadas, enunciados muito curtos e questões que dependem de
figura/imagem (o texto da figura se perde na conversão).

## Limitações

- **Provas descartadas.** Muitas provas ainda não geram questões: gabarito de vários cargos sem como
  identificar o cargo, gabarito que na verdade é outro caderno, formatos de alternativas não reconhecidos
  e seções específicas não encontradas (motivos e contagens em `descartes.csv`).
- **Subárea inferida do nome da prova**, com prioridade seguranca > redes > sistemas (a mesma das
  listagens do scraper). Provas de "infraestrutura e segurança" contam como `seguranca`. Provas de
  Embrapa/ciências agrárias foram excluídas (sistemas de produção, não TI). Concursos de TI mais amplos
  podem trazer questões de outras áreas de TI dentro da mesma prova.
- **Itens certo/errado** (Cebraspe) são afirmações soltas, mais curtas, e não têm alternativas reais. Os
  enunciados de itens de um mesmo bloco podem perder o texto-base compartilhado.
- **Ano** vem do nome da prova, não da data de aplicação.
- **Gabarito**: usado o definitivo quando existe, senão o último disponível. As verificações são
  automáticas (cobertura e distribuição das letras) mais amostras conferidas à mão; não há revisão
  completa.
- Questões com tabelas ou código podem ter formatação degradada pelo `pdftotext`; questões que dependem
  de figura foram descartadas.

## Uso e direitos

Material de provas públicas, coletado para fins acadêmicos. Os direitos pertencem às bancas
organizadoras e ao PCI Concursos; verifique os termos de uso antes de redistribuir.
