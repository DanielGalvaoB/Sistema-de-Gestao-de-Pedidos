from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.core.errors import register_exception_handlers
from app.core.imagens import PREFIXO_URL, pasta_uploads
from app.routers import (
    auth_router,
    categoria_router,
    contas_router,
    estabelecimentos_router,
    financeiro_router,
    menu_router,
    mesas_router,
    pedido_router,
    public_router,
    relatorios_router,
    usuarios_router,
    ws_router,
)

# O schema do banco e criado/atualizado SOMENTE pelo Alembic:
#   alembic upgrade head
app = FastAPI(title='PDV API', version='1.0.0')

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
    expose_headers=['Content-Disposition', 'X-Resultado'],
)
register_exception_handlers(app)

app.include_router(auth_router.router)
app.include_router(usuarios_router.router)
app.include_router(estabelecimentos_router.router)
app.include_router(categoria_router.router)
app.include_router(menu_router.router)
app.include_router(mesas_router.router)
app.include_router(pedido_router.router)
app.include_router(contas_router.router)
app.include_router(financeiro_router.router)
app.include_router(relatorios_router.router)
app.include_router(public_router.router)
app.include_router(ws_router.router)


# Imagens dos produtos (somente arquivos regravados pelo servidor)
app.mount(PREFIXO_URL, StaticFiles(directory=pasta_uploads()), name='uploads')


@app.get('/health', tags=['infra'])
def health():
    return {'status': 'ok'}
