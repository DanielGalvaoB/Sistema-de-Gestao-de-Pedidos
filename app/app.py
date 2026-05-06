from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import (
    categoria_router,
    estabelecimentos_router,
    menu_router,
    pedido_router,
)

Base.metadata.create_all(bind=engine)

app = FastAPI(title='PDV API')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar: ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(estabelecimentos_router.router)
app.include_router(categoria_router.router)
app.include_router(menu_router.router)
app.include_router(pedido_router.router)
