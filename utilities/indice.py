from collections import OrderedDict
from threading import Lock

from src.geohash import encode_geohash
from src.trie import Trie_Compacta
from utilities.files import criar_entregadores


# Cada geração tem seu próprio índice. O limite evita acumular frotas na memória.
_MAX_GERACOES = 8
_indices = OrderedDict()
_lock = Lock()


def obter_trie_entregadores(geracao, registros):
    """Reutiliza a Trie da geração; reconstrói se ela saiu da memória do servidor."""
    if not geracao:
        raise ValueError("Geração dos entregadores não informada.")

    # Evita que callbacks simultâneos construam duas Tries para a mesma geração.
    with _lock:
        if geracao in _indices:
            _indices.move_to_end(geracao)
            return _indices[geracao]

        trie = Trie_Compacta()
        for entregador in criar_entregadores(registros):
            entregador.geohash = encode_geohash(
                entregador.latitude, entregador.longitude
            )
            trie.insert(entregador)

        _indices[geracao] = trie
        if len(_indices) > _MAX_GERACOES:
            _indices.popitem(last=False)

        return trie
