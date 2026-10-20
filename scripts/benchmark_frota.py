from statistics import mean
from time import perf_counter

import pandas as pd

from src.grafo import obter_malha
from src.simulador import corrigir_para_ruas, gerar_entregadores_normais
from utilities.constants import DATA_DIR


def main():
    bares = pd.read_csv(DATA_DIR / "bares.csv").dropna(subset=["GEOMETRIA"])
    print(f"Restaurantes: {len(bares)} | Carregando malha...", flush=True)
    grafo = obter_malha()
    resultados = []
    for quantidade in [1000, 10000, 100000, 1000000]:
        print(f"Testando N={quantidade}...", flush=True)
        tempos_geracao = []
        tempos_correcao = []
        for _ in range(5):
            inicio = perf_counter()
            frota = gerar_entregadores_normais(bares, quantidade)
            tempos_geracao.append(perf_counter() - inicio)
            assert len(frota) == quantidade, "Quantidade gerada diferente da solicitada."

            inicio = perf_counter()
            frota_corrigida = corrigir_para_ruas(frota, grafo)
            tempos_correcao.append(perf_counter() - inicio)
            assert len(frota_corrigida) == quantidade, "A correcao alterou a quantidade."
            del frota, frota_corrigida

        resultados.append({
            "quantidade": quantidade,
            "geracao_media_s": mean(tempos_geracao),
            "correcao_media_s": mean(tempos_correcao),
        })

    resultados = pd.DataFrame(resultados)
    arquivo = DATA_DIR / "benchmark_frota.csv"
    resultados.to_csv(arquivo, index=False)
    print(resultados.to_string(index=False))
    print(f"Resultados salvos em {arquivo}")


if __name__ == "__main__":
    main()