# Dataset Card — Questões de concursos de TI (redes, segurança, sistemas)

Questões objetivas de **conhecimentos específicos** de concursos públicos brasileiros da área de TI,
coletadas do [PCI Concursos](https://www.pciconcursos.com.br) para o Trabalho 1 de PLN (PUCRS).
Cada questão traz enunciado, alternativas e gabarito, e está classificada por subárea e ano.

## Conteúdo

```
dataset/
├── raw.zip         96 .txt compactados (saída de `pdftotext -layout`): provas e gabaritos, um por PDF
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
| `tipo`         | `multipla_escolha` (hoje todas) ou `certo_errado`                           |
| `enunciado`    | texto do enunciado, sem as alternativas                                     |
| `alternativas` | objeto letra → texto (`{"A": "...", "B": "..."}`), 4 ou 5 alternativas      |
| `gabarito`     | letra da alternativa correta                                                |

## Estatísticas

274 questões, vindas de 13 provas. Estatísticas completas do corpus (tokens, vocabulário, tamanho
dos textos, distribuição do gabarito, palavras mais frequentes e características por subárea) em
[`ESTATISTICAS.md`](ESTATISTICAS.md), geradas por `scraper/estatisticas_dataset.py`.

| subárea   | 2023 | 2024 | 2025 | 2026 | total | provas |
|-----------|-----:|-----:|-----:|-----:|------:|-------:|
| redes     |    – |   69 |    – |    – |    69 |      2 |
| seguranca |   25 |   75 |    7 |   28 |   135 |      8 |
| sistemas  |   28 |   17 |    – |   25 |    70 |      3 |

140 questões têm 5 alternativas e 134 têm 4. Todas são de múltipla escolha.

## Como foi construído

1. **Coleta**: `scraper/scraper_pci.py` baixa provas e gabaritos (PDF) das listagens de cada subárea.
2. **Texto**: `pdftotext -layout` em todos os PDFs → `raw.zip`.
3. **Processamento**: `scraper/processar_dataset.py`:
   - separa as colunas de cada página (o `-layout` intercala provas em duas colunas);
   - remove cabeçalhos, rodapés e marcas do site;
   - recorta a seção de conhecimentos específicos;
   - segmenta as questões e separa enunciado de alternativas;
   - junta o gabarito pelo número da questão.

Para regenerar: `python3 scraper/processar_dataset.py` (lê `dataset/raw.zip`, grava em `dataset/`).

## Filtros (ver `descartes.csv`)

Descartadas: caracteres corrompidos pela conversão, questões sem alternativas identificáveis, sem
resposta no gabarito, anuladas, duplicadas, enunciados muito curtos e questões que dependem de
figura/imagem (o texto da figura se perde na conversão).

## Limitações

- **Cobertura baixa e desbalanceada.** Só 13 das provas geraram questões; `redes` vem de **duas
  provas**, ambas de 2024. Muitas provas foram descartadas porque o gabarito cobre vários cargos e o parser não
  consegue escolher a tabela do cargo certo (Cebraspe, FCPC, Comperve etc.), ou porque o número da
  questão não aparece no gabarito lido.
- **Subárea inferida do nome da prova**, com prioridade seguranca > redes > sistemas (a mesma das
  listagens do scraper). Provas de "infraestrutura e segurança" contam como `seguranca`. Provas de
  Embrapa/ciências agrárias foram excluídas (sistemas de produção, não TI).
- **Ano** vem do nome da prova, não da data de aplicação.
- **Gabarito**: usado o definitivo quando existe, senão o último disponível. Foram conferidas à mão
  só algumas amostras; não há revisão completa.
- Questões com tabelas ou código podem ter formatação degradada pelo `pdftotext`.

## Uso e direitos

Material de provas públicas, coletado para fins acadêmicos. Os direitos pertencem às bancas
organizadoras e ao PCI Concursos; verifique os termos de uso antes de redistribuir.
