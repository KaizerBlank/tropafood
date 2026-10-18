from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"

CSV_BARES = DATA_DIR / "100_bares.csv"
CSV_ENTREGADORES_MATEMATICOS = DATA_DIR / "entregadores_matematicos.csv"
CSV_ENTREGADORES_CORRIGIDOS = DATA_DIR / "entregadores_corrigidos.csv"

DESVIO_PADRAO_METROS = 400.0
CRS_METROS = "EPSG:31983"
CRS_GRAUS = "EPSG:4326"