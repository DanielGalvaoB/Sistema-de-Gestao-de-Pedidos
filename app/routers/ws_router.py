import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from app.core import realtime
from app.dependencies.auth_dep import DbSession, usuario_do_token

router = APIRouter(tags=['tempo real'])


@router.websocket('/ws/pedidos')
async def ws_pedidos(websocket: WebSocket, token: str, db: DbSession):
    """Envia {"evento": "atualizar", "versao": N} quando pedidos mudam.

    O cliente deve recarregar os dados pela API REST ao receber o evento.
    """
    user = usuario_do_token(db, token)
    id_estab = user.id_estabelecimento if user else None
    # Libera a conexao: o loop abaixo nao acessa o banco
    db.close()
    if id_estab is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    ultima = realtime.versao(id_estab)
    await websocket.send_json({'evento': 'conectado', 'versao': ultima})
    try:
        while True:
            await asyncio.sleep(1)
            atual = realtime.versao(id_estab)
            if atual != ultima:
                ultima = atual
                await websocket.send_json({
                    'evento': 'atualizar',
                    'versao': atual,
                })
    except (WebSocketDisconnect, RuntimeError):
        return
