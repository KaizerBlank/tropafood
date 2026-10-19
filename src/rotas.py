import osmnx as ox
from shapely.geometry import LineString, Point
from itertools import count

def obter_geometria_aresta(grafo, u, v, key):
    dados = grafo.edges[u, v, key]

    linha = dados.get("geometry")

    if linha is None:
        linha = LineString([
            (grafo.nodes[u]["x"], grafo.nodes[u]["y"]),
            (grafo.nodes[v]["x"], grafo.nodes[v]["y"]),
        ])

    ponto_u = Point(
        grafo.nodes[u]["x"],
        grafo.nodes[u]["y"],
    )

    inicio = Point(linha.coords[0])
    fim = Point(linha.coords[-1])

    if ponto_u.distance(fim) < ponto_u.distance(inicio):
        linha = LineString(list(linha.coords)[::-1])

    return linha

def localizar_na_via(grafo, x, y, aresta=None):
    if aresta is None:
        encontrada = ox.distance.nearest_edges(
            grafo,
            X=[x],
            Y=[y],
        )[0]

        aresta = tuple(int(valor) for valor in encontrada)

    u, v, key = aresta

    linha = obter_geometria_aresta(
        grafo,
        u,
        v,
        key,
    )

    posicao = float(linha.project(Point(x, y)))

    # Corrige pequenas diferenças numericas nos extremos.
    if posicao < 1e-6:
        posicao = 0.0
    elif linha.length - posicao < 1e-6:
        posicao = float(linha.length)

    ponto = linha.interpolate(posicao)

    return {
        "aresta": aresta,
        "x": ponto.x,
        "y": ponto.y,
        "posicao_geometria_metros": posicao,
        "comprimento_geometria_metros": float(linha.length),
        "comprimento_rota_metros": float(
            grafo.edges[u, v, key]["length"]
        ),
    }

def obter_sentidos_permitidos(grafo, localizacao):
    u, v, key = localizacao["aresta"]

    linha_original = obter_geometria_aresta(
        grafo, u, v, key
    )

    arestas = [(u, v, key)]

    for chave in grafo.get_edge_data(v, u, default={}):
        inversa = (v, u, chave)

        if inversa == (u, v, key):
            continue

        linha_inversa = obter_geometria_aresta(
            grafo, *inversa
        )

        if linha_original.equals(linha_inversa):
            arestas.append(inversa)

    sentidos = {}

    for aresta in arestas:
        ponto = localizar_na_via(
            grafo,
            localizacao["x"],
            localizacao["y"],
            aresta=aresta,
        )

        comprimento = ponto["comprimento_geometria_metros"]

        fracao = (
            ponto["posicao_geometria_metros"] / comprimento
            if comprimento > 0 else 0.0
        )

        sentidos[aresta] = (
            fracao * ponto["comprimento_rota_metros"]
        )

    return sentidos

def calcular_distancias_osmnx(grafo, origens, destino):
    if not grafo.is_directed():
        raise ValueError("O cálculo exige um grafo dirigido.")

    if not origens:
        return []

    temporario = grafo.copy()
    identificadores = count(-1, -1)

    def criar_no(localizacao):
        no = next(identificadores)

        while no in temporario:
            no = next(identificadores)

        temporario.add_node(
            no,
            x=localizacao["x"],
            y=localizacao["y"],
        )

        return no

    sentidos_destino = obter_sentidos_permitidos(
        grafo, destino
    )

    no_destino = criar_no(destino)

    # Liga as ruas ao ponto de destino
    for aresta, posicao in sentidos_destino.items():
        u, v, key = aresta

        comprimento = float(
            grafo.edges[u, v, key]["length"]
        )

        temporario.add_edge(
            u, no_destino, length=posicao
        )

        if posicao == comprimento:
            temporario.add_edge(
                v, no_destino, length=0.0
            )

    nos_origem = []

    for origem in origens:
        no_origem = criar_no(origem)
        nos_origem.append(no_origem)

        sentidos_origem = obter_sentidos_permitidos(
            grafo, origem
        )

        for aresta, posicao in sentidos_origem.items():
            u, v, key = aresta

            comprimento = float(
                grafo.edges[u, v, key]["length"]
            )

            # Trecho entre o entregador e o fim da aresta
            temporario.add_edge(
                no_origem,
                v,
                length=comprimento - posicao,
            )

            if posicao == 0.0:
                temporario.add_edge(
                    no_origem, u, length=0.0
                )

            # Origem e destino podem estar na mesma rua
            posicao_destino = sentidos_destino.get(aresta)

            if (
                posicao_destino is not None
                and posicao_destino >= posicao
            ):
                temporario.add_edge(
                    no_origem,
                    no_destino,
                    length=posicao_destino - posicao,
                )

    caminhos = ox.routing.shortest_path(
        temporario,
        orig=nos_origem,
        dest=[no_destino] * len(nos_origem),
        weight="length",
        cpus=1,
    )

    distancias = []

    for caminho in caminhos:
        if caminho is None:
            distancias.append(None)
            continue

        distancia = sum(
            min(
                float(dados["length"])
                for dados in temporario.get_edge_data(
                    u, v
                ).values()
            )
            for u, v in zip(caminho, caminho[1:])
        )

        distancias.append(float(distancia))

    return distancias