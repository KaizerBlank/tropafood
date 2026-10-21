import csv
import gzip
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import re
import statistics
import sys
from time import perf_counter

sys.path.insert(0, '/app')
import numpy as np
from osmnx.distance import great_circle
import app

SAIDA = Path('/experimento/saidas')
SAIDA.mkdir(exist_ok=True)
SEMENTE = 20261020
REPETICOES = 5
CASOS = [
    ('C1', 1000, 3, 1000),
    ('C2', 5000, 3, 1000),
    ('C3', 5000, 3, 2000),
    ('C4', 5000, 0, 2000),
    ('C5', 5000, 3, 100),
]


def salvar_json(nome, valor):
    (SAIDA / nome).write_text(json.dumps(valor, ensure_ascii=False, indent=2))


def salvar_csv(nome, registros):
    with (SAIDA / nome).open('w', encoding='utf-8', newline='') as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=list(registros[0]), lineterminator='\n')
        escritor.writeheader()
        escritor.writerows(registros)


def linhas_tabela(componente):
    if isinstance(componente, dict):
        filhos = componente.get('props', {}).get('children', [])
        if componente.get('type') == 'Tr' and isinstance(filhos, list):
            if filhos and filhos[0].get('type') == 'Td':
                yield [td['props']['children'] for td in filhos]
                return
        yield from linhas_tabela(filhos)
    elif isinstance(componente, list):
        for filho in componente:
            yield from linhas_tabela(filho)


def consulta(cliente, registros, geracao, restaurante, raio):
    inicio = perf_counter()
    resposta_mapa = cliente.post('/_dash-update-component', json={
        'output': '..mapa-entregadores.figure...resumo-busca.children..',
        'outputs': [
            {'id': 'mapa-entregadores', 'property': 'figure'},
            {'id': 'resumo-busca', 'property': 'children'},
        ],
        'inputs': [
            {'id': 'dados-entregadores', 'property': 'data', 'value': registros},
            {'id': 'busca-restaurante', 'property': 'value', 'value': restaurante},
            {'id': 'raio-busca', 'property': 'value', 'value': raio},
            {'id': 'exibir-raio', 'property': 'value', 'value': ['exibir']},
            {'id': 'exibir-restaurantes', 'property': 'value', 'value': []},
            {'id': 'geracao-entregadores', 'property': 'data', 'value': geracao},
        ],
        'state': [],
        'changedPropIds': ['busca-restaurante.value', 'raio-busca.value'],
    })
    fim_mapa = perf_counter()
    resposta_tabela = cliente.post('/_dash-update-component', json={
        'output': 'tabela-rotas.children',
        'outputs': {'id': 'tabela-rotas', 'property': 'children'},
        'inputs': [
            {'id': 'dados-entregadores', 'property': 'data', 'value': registros},
            {'id': 'busca-restaurante', 'property': 'value', 'value': restaurante},
            {'id': 'raio-busca', 'property': 'value', 'value': raio},
            {'id': 'geracao-entregadores', 'property': 'data', 'value': geracao},
        ],
        'state': [],
        'changedPropIds': ['busca-restaurante.value', 'raio-busca.value'],
    })
    fim_tabela = perf_counter()
    assert resposta_mapa.status_code == 200, resposta_mapa.data[:1000]
    assert resposta_tabela.status_code == 200, resposta_tabela.data[:1000]
    mapa = resposta_mapa.get_json()['response']
    tabela = resposta_tabela.get_json()['response']['tabela-rotas']['children']
    resumo = mapa['resumo-busca']['children']
    encontrados = int(re.search(r'^(\d+) de ', resumo).group(1))
    linhas = list(linhas_tabela(tabela))
    assert len(linhas) == encontrados, (resumo, tabela)

    # Referência independente da Trie: conferir o raio sobre toda a frota.
    # A validação ocorre depois de encerrar a medição dos callbacks.
    bar = app.df_bares.iloc[restaurante]
    distancias = great_circle(
        bar['LATITUDE'], bar['LONGITUDE'],
        np.array([e['latitude_rua_graus'] for e in registros]),
        np.array([e['longitude_rua_graus'] for e in registros]),
    )
    esperados = {
        e['id_entregador'] for e, distancia in zip(registros, distancias)
        if distancia <= raio
    }
    ids_tabela = {linha[0] for linha in linhas}
    pontos = next(t for t in mapa['mapa-entregadores']['figure']['data']
                  if t.get('name') == 'Entregadores')
    cores = pontos['marker']['color']
    assert len(cores) == len(registros)
    ids_verdes = {
        e['id_entregador'] for e, cor in zip(registros, cores) if cor == 'green'
    }
    assert ids_tabela == esperados, ('Tabela', esperados - ids_tabela, ids_tabela - esperados)
    assert ids_verdes == esperados, ('Mapa', esperados - ids_verdes, ids_verdes - esperados)
    return {
        'mapa_s': fim_mapa - inicio,
        'tabela_s': fim_tabela - fim_mapa,
        'total_sequencial_s': fim_tabela - inicio,
    }, linhas


ambiente = {
    'data_local': '2026-10-20',
    'host': {'cpu': 'Apple M4', 'memoria_gib': 16, 'nucleos': 10,
             'sistema': 'macOS 27.0.1'},
    'container': {'sistema': platform.platform(), 'python': platform.python_version(),
                  'cpus_visiveis': os.cpu_count()},
    'pacotes': {p: importlib.metadata.version(p) for p in ['dash', 'plotly', 'osmnx', 'pandas', 'numpy', 'shapely']},
    'semente_base': SEMENTE,
    'repeticoes_por_consulta': REPETICOES,
    'restaurantes': len(app.df_bares),
    'validacao': 'IDs da tabela e dos marcadores verdes comparados ao cálculo do raio sobre toda a frota, sem usar a Trie como referência; validação fora da janela de medição.',
    'metodo': 'Dois POSTs em sequência ao servidor Dash por Flask.test_client, com execução real dos callbacks. Tempo inclui serialização local, mapa/resumo e tabela/rotas; exclui geração, indexação inicial, aquecimento, trânsito de rede e renderização no navegador. A tabela inclui a leitura e preparação da malha em cada consulta não vazia, conforme a aplicação.',
}
for nome in ['cpu.max', 'memory.max']:
    p = Path('/sys/fs/cgroup') / nome
    if p.exists():
        ambiente['container'][nome] = p.read_text().strip()
salvar_json('ambiente.json', ambiente)

frotas = {}
preparacoes = []
for quantidade in [1000, 5000]:
    np.random.seed(SEMENTE + quantidade)
    inicio = perf_counter()
    registros, mensagem, geracao = app.atualizar_mapa(1, quantidade, [])
    duracao = perf_counter() - inicio
    assert isinstance(registros, list) and len(registros) == quantidade, mensagem
    frotas[quantidade] = (registros, geracao)
    dados = json.dumps(registros, ensure_ascii=False, separators=(',', ':')).encode()
    (SAIDA / f'frota_{quantidade}.json.gz').write_bytes(gzip.compress(dados, mtime=0))
    preparacoes.append({'quantidade': quantidade, 'semente': SEMENTE + quantidade,
                        'preparacao_s': duracao, 'mensagem': mensagem})
    print(f'Frota N={quantidade} preparada em {duracao:.3f}s.', flush=True)
salvar_json('preparacoes.json', preparacoes)

cliente = app.app.server.test_client()
resumos = []
brutos = []
for caso, quantidade, idx, raio in CASOS:
    restaurante = app.df_bares.iloc[idx]
    registros, geracao = frotas[quantidade]
    por_id = {str(e['id_entregador']): e for e in registros}
    print(f'{caso}: N={quantidade}, {restaurante["NOME"]}, raio={raio}m. Aquecimento...', flush=True)
    _, referencia = consulta(cliente, registros, geracao, idx, raio)
    tempos = []
    for repeticao in range(1, REPETICOES + 1):
        medidas, linhas = consulta(cliente, registros, geracao, idx, raio)
        assert linhas == referencia
        tempos.append(medidas)
        brutos.append({'caso': caso, 'repeticao': repeticao, **medidas})
        print(f'  repetição {repeticao}: {medidas["total_sequencial_s"]:.3f}s, {len(linhas)} selecionados.', flush=True)
    detalhados = []
    for identificador, latitude, longitude, distancia, tempo in referencia:
        origem = por_id[str(identificador)]
        geografica = float(great_circle(
            restaurante['LATITUDE'], restaurante['LONGITUDE'],
            origem['latitude_rua_graus'], origem['longitude_rua_graus'],
        ))
        assert geografica <= raio + 1e-6
        detalhados.append({
            'id_entregador': identificador,
            'latitude': origem['latitude_rua_graus'],
            'longitude': origem['longitude_rua_graus'],
            'distancia_geografica_m': geografica,
            'distancia_viaria_m': None if distancia == 'Sem rota' else float(distancia),
            'tempo_exibido': tempo,
        })
    distancias = [e['distancia_viaria_m'] for e in detalhados if e['distancia_viaria_m'] is not None]
    assert distancias == sorted(distancias)
    resumo = {
        'caso': caso, 'frota': quantidade, 'restaurante_indice': idx,
        'restaurante_id': int(restaurante['_id']), 'restaurante': str(restaurante['NOME']),
        'bairro': str(restaurante['NOME_BAIRRO']), 'raio_m': raio,
        'selecionados': len(detalhados), 'com_rota': len(distancias),
        'sem_rota': len(detalhados) - len(distancias),
        'rotas_maiores_que_raio': sum(d > raio for d in distancias),
        'rota_min_m': min(distancias) if distancias else None,
        'rota_max_m': max(distancias) if distancias else None,
        'mapa_media_s': statistics.mean(t['mapa_s'] for t in tempos),
        'tabela_media_s': statistics.mean(t['tabela_s'] for t in tempos),
        'total_media_s': statistics.mean(t['total_sequencial_s'] for t in tempos),
        'total_min_s': min(t['total_sequencial_s'] for t in tempos),
        'total_max_s': max(t['total_sequencial_s'] for t in tempos),
        'total_desvio_s': statistics.stdev(t['total_sequencial_s'] for t in tempos),
    }
    salvar_json(f'{caso}_resultados.json', detalhados)
    resumos.append(resumo)
    salvar_json('resumo.json', resumos)
    salvar_csv('resultados_consultas.csv', resumos)
    salvar_csv('tempos_brutos.csv', brutos)
    print(f'{caso} concluído: média {resumo["total_media_s"]:.3f}s; {resumo["rotas_maiores_que_raio"]} rotas maiores que o raio.', flush=True)

print('Experimentos concluídos.', flush=True)
