from pathlib import Path
import osmnx as ox

ox.settings.log_console = True

def obter_malha():
    pasta = Path(__file__).resolve().parent.parent / "data"
    pasta.mkdir(parents=True, exist_ok=True)

    arquivo = pasta / "malha_bh_drive_31983.graphml"

    if arquivo.exists():
        return ox.io.load_graphml(arquivo)

    # Gera o grafo da malha viaria de BH
    grafo = ox.graph.graph_from_place(
        "Belo Horizonte, Minas Gerais, Brasil",
        network_type = "drive",
        simplify = True,
        retain_all = True,
    )

    # Reprojeta para SIRGAS 2000 para trabalharmos com metros
    grafo = ox.projection.project_graph(
        grafo,
        to_crs = "EPSG:31983",
    )

    ox.io.save_graphml(grafo, arquivo)
    
    return grafo