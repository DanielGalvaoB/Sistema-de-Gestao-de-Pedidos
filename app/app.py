from fastapi import FastAPI

from app.database import Base, engine
from app.routers import (
    categoria_router,
    estabelecimentos_router,
    menu_router,
    pedido_router,
)

Base.metadata.create_all(bind=engine)

app = FastAPI(title='PDV API')

app.include_router(estabelecimentos_router.router)
app.include_router(categoria_router.router)
app.include_router(menu_router.router)
app.include_router(pedido_router.router)
