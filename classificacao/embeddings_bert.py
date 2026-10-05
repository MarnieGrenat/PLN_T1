# Gera (ou carrega do cache) os embeddings de BERT das questões.
#
# Usado pelo classificar.py e também pode ser rodado sozinho, por exemplo no Google Colab com GPU:
#   python classificacao/embeddings_bert.py
# Os arquivos .npy ficam em classificacao/cache/. O nome do arquivo inclui um hash dos textos, então um
# cache gerado com outra versão do dataset nunca é reaproveitado por engano.

import hashlib
import os

import numpy as np

from preparar_dados import carregar_questoes

PASTA_CACHE = "classificacao/cache"
MODELOS_BERT = ["neuralmind/bert-base-portuguese-cased", "bert-base-uncased"]


def hash_textos(textos):
    return hashlib.sha1("\n".join(textos).encode("utf-8")).hexdigest()[:10]


def arquivo_cache(nome_modelo, textos):
    return f"{PASTA_CACHE}/{nome_modelo.replace('/', '_')}_{hash_textos(textos)}.npy"


def gerar_embeddings_bert(nome_modelo, textos):
    os.makedirs(PASTA_CACHE, exist_ok=True)
    caminho = arquivo_cache(nome_modelo, textos)
    if os.path.exists(caminho):
        print("Usando embeddings salvos em", caminho)
        return np.load(caminho)

    import torch
    from transformers import AutoTokenizer, AutoModel

    dispositivo = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Gerando embeddings com {nome_modelo} em {dispositivo}")
    tokenizador = AutoTokenizer.from_pretrained(nome_modelo)
    modelo = AutoModel.from_pretrained(nome_modelo).to(dispositivo)
    modelo.eval()

    embeddings = []
    with torch.no_grad():  # não estamos treinando o BERT, só usando
        for i in range(0, len(textos), 16):  # de 16 em 16 textos
            lote = textos[i:i + 16]
            entrada = tokenizador(lote, padding=True, truncation=True, max_length=512, return_tensors="pt").to(dispositivo)
            saida = modelo(**entrada).last_hidden_state  # um vetor de 768 posições por token

            # média dos vetores dos tokens, ignorando o padding (attention_mask = 0)
            mascara = entrada["attention_mask"].unsqueeze(-1)
            media = (saida * mascara).sum(dim=1) / mascara.sum(dim=1)
            embeddings.append(media.cpu().numpy())
            print(f"  {min(i + 16, len(textos))}/{len(textos)} questões", end="\r")
    print()

    X = np.vstack(embeddings)
    np.save(caminho, X)
    return X


if __name__ == "__main__":
    df = carregar_questoes()
    textos = list(df["texto"])
    for nome in MODELOS_BERT:
        X = gerar_embeddings_bert(nome, textos)
        print(nome, X.shape)
