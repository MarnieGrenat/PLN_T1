# Prompt: anotação de similaridade pelo Claude (item 4.a.iii)

Você vai atuar como anotador de um dataset de similaridade semântica de palavras do domínio de
Tecnologia da Informação. A nota tem que ser o **seu próprio julgamento** sobre o significado das palavras.

**Regras (importantes para a validade do experimento):**

- Leia **somente** estes dois arquivos:
  - `similaridade/topico_4/claude/entrada_nosso.csv`
  - `similaridade/topico_4/claude/entrada_aula.csv`
- **Não abra nenhum outro arquivo do repositório**, nem rode `git log`/`git diff`/`grep` fora desta pasta.
  Outros arquivos têm as notas dos anotadores humanos e ver essas notas invalida a comparação.
- Não use código, embeddings, outros modelos nem busca na web para calcular as notas. Pode usar código só
  para ler e escrever os CSVs.
- Avalie cada par de forma independente. Não ajuste as notas para seguir uma distribuição.

**Tarefa 1: `entrada_nosso.csv` (100 pares)**

Para cada par, avalie o quanto as duas palavras são similares em significado. Use a escala Likert de 1 a 5
(só números inteiros):

1 = Totalmente dissimilar (ou Muito diferente)
2 = Parcialmente dissimilar (ou Um pouco diferente)
3 = Neutro / Indiferente (Nem similar, nem dissimilar)
4 = Parcialmente similar (ou Um pouco parecido)
5 = Totalmente similar (ou Muito parecido)

Salve em `similaridade/topico_4/claude/respostas_nosso.csv`.

**Tarefa 2: `entrada_aula.csv` (80 pares)**

Para cada par, avalie o quanto as duas palavras são similares em significado. Use uma nota de 0 a 1, só com
os valores 0, 0.25, 0.5, 0.75 ou 1:
0 = nada similar, 0.5 = similaridade intermediária, 1 = mesmo significado.

Salve em `similaridade/topico_4/claude/respostas_aula.csv`.

**Formato das respostas:** CSV UTF-8, separado por vírgula, com o cabeçalho `id,palavra_1,palavra_2,nota`,
uma linha por par, na mesma ordem e com os mesmos ids do arquivo de entrada. Ponto como separador decimal
(ex.: `0.75`).

**Ao terminar:**

1. Confira que `respostas_nosso.csv` tem 100 linhas e `respostas_aula.csv` tem 80, com todos os ids e todas
   as notas dentro da escala.
2. Crie `similaridade/topico_4/claude/MODELO.txt` com o nome exato do modelo que você é e a data de hoje.
3. Não altere nenhum outro arquivo e não faça commit.
