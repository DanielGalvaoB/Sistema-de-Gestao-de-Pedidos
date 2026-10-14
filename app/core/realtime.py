"""Sinalizacao simples de mudancas para o painel em tempo real.

As rotas sincronas incrementam uma versao por estabelecimento; o handler de
WebSocket observa essa versao e avisa os clientes conectados, que entao
recarregam os dados pela API REST. Funciona em processo unico (uvicorn sem
workers multiplos). Para varios processos, trocar por Redis pub/sub.
"""

import threading
from collections import defaultdict

_lock = threading.Lock()
_versoes: dict[int, int] = defaultdict(int)


def notificar(id_estabelecimento: int) -> None:
    with _lock:
        _versoes[id_estabelecimento] += 1


def versao(id_estabelecimento: int) -> int:
    with _lock:
        return _versoes[id_estabelecimento]
