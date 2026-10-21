import sys
sys.path.insert(0, '/app')
import numpy as np
import app

gerar_original = app.gerar_entregadores_normais


def gerar_com_semente(df_bares, N_entregadores, desvio_padrao_metros):
    np.random.seed(20261020 + N_entregadores)
    return gerar_original(df_bares, N_entregadores, desvio_padrao_metros)


# Somente neste processo de documentação: repetir as frotas medidas no benchmark.
app.gerar_entregadores_normais = gerar_com_semente
app.app.run(host='0.0.0.0', port=8051, debug=False, use_reloader=False)
