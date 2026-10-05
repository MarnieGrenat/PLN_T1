# Uso de ferramentas de IA

Declaração do uso de IA no Trabalho 1, como pede o enunciado. Agentes de Inteligência Artificial foram usados das seguintes formas:

1. **Como objeto de estudo**, no item 4.a.iii, que pede um LLM para medir similaridade de palavras.
2. **Como ferramenta de desenvolvimento**, como ferramenta geradora de código e documentação.
3. **Revisor de requisitos**, revisando o enunciado do trabalho e o trabalho final, garantindo que todos os requisitos fossem cumpridos.

## 1. IA como objeto de estudo (item 4)

| ferramenta | uso | onde está registrado |
|---|---|---|
| Claude Opus 5.5 (Anthropic) | deu as notas de similaridade aos 100 pares do nosso dataset e aos 80 do dataset da aula | [`similaridade/topico_4/claude/`](similaridade/topico_4/claude/) |
| Gemini (Google AI Studio, API gratuita) | tentativa de um segundo LLM. A API respondeu 503 (sobrecarregada), e o Gemini ficou fora da comparação | seção 3.2 do notebook `similaridade/topico_4/similaridade_modelos.ipynb` |

Para que a comparação com os humanos fosse válida, o LLM anotou **às cegas**:
- Uma sessão separada do Claude recebeu o prompt de
  [`PROMPT.md`](similaridade/topico_4/claude/PROMPT.md).
- Essa sessão só podia ler os arquivos de entrada, que têm apenas os pares, sem as notas humanas.
- As instruções e as escalas eram as mesmas dadas aos anotadores.
- O registro da sessão está em [`Retorno_Claude.md`](similaridade/topico_4/claude/Retorno_Claude.md), e o modelo e a
  data em [`MODELO.txt`](similaridade/topico_4/claude/MODELO.txt).

As notas vieram de conversas, não de chamadas de API pelo código. Por isso não são reproduzíveis rodando o notebook,
mas ficam registradas nesses arquivos.

## 2. IA como ferramenta de desenvolvimento

Usamos o **Claude Code** (assistente de programação da Anthropic), com os modelos Claude Sonnet 5.5 e Claude Opus 5.5.

| parte do trabalho | o que a IA fez                                                                                                                                                                                                                          |
|---|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Corpus de questões (item 1) | código de processamento do texto (`scraper/processar_dataset.py`) e das estatísticas (`scraper/estatisticas_dataset.py`), *dataset card* (`dataset/README.md`) e `ESTATISTICAS.md`. |
| Corpus de similaridade (item 2) | scripts de construção dos pares (`construir_pares.py`) e de concordância (`avaliar_concordancia.py`), `CONCORDANCIA.md` e *dataset card*                                                                                                |
| Classificação (item 3) | reorganização do código em `preparar_dados.py` e `embeddings_bert.py`, notebook do Colab, geração dos resultados e documentação                                                                                                         |
| Similaridade com modelos (item 4) | texto de análise em `similaridade/COMPARACAO.md`                                                                                              |
| Documentação geral | Utilizado para sintetizar nossas ideias de forma profissional nos arquivos markdown                                                                                                                                                     |                                                                                               |

O que **não** foi feito por IA:
- **Anotações manuais de similaridade** (`similaridade/pares_gabriela.csv` e `similaridade/pares_renato.csv`):
  cada aluno deu as próprias notas, sem ver as do outro e sem sugestão de modelo. Alguns desses arquivos foram
  adicionados ao repositório em commits feitos pelo Claude Code, mas as notas são dos alunos.
- **Dataset da aula** (`similaridade/topico_4/dataset_aula.csv`): feito em aula.
- **Scraping de questões** foi feito de forma parcialmente manual devido reCAPTCHA.
- **Análise e Correção de código** O código foi parcialmente escrito pelos alunos durante revisões.

Todo o código e o texto produzidos com IA foram revisados pelo grupo, que responde pelo conteúdo do trabalho.
