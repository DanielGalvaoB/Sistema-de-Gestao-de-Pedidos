"""Rotas publicas: cardapio digital, envio e acompanhamento de pedidos."""

from fastapi import APIRouter, status
from pydantic import BaseModel

from app.core.errors import BusinessRuleError
from app.crud import (
    categoria_crud,
    estabelecimento_crud,
    menu_crud,
    mesa_crud,
    pedido_crud,
)
from app.dependencies.auth_dep import DbSession
from app.schemas.categoria_schema import CategoriaResponse
from app.schemas.estabelecimento_schema import EstabelecimentoPublico
from app.schemas.menu_schema import MenuResponse
from app.schemas.pedido_schema import PedidoAcompanhamento, PedidoPublicoCreate

router = APIRouter(prefix='/public', tags=['publico'])


class CategoriaComProdutos(CategoriaResponse):
    produtos: list[MenuResponse]


class CardapioPublico(BaseModel):
    estabelecimento: EstabelecimentoPublico
    mesa_numero: str | None
    categorias: list[CategoriaComProdutos]


class PedidoEnviado(BaseModel):
    numero: int
    codigo_acompanhamento: str


@router.get('/{slug}', response_model=CardapioPublico)
def cardapio(slug: str, db: DbSession, mesa: str | None = None):
    estab = estabelecimento_crud.get_por_slug(db, slug)
    mesa_numero = None
    if mesa:
        mesa_numero = mesa_crud.get_mesa_por_token(db, estab.id, mesa).numero
    produtos = menu_crud.list_menu(db, estab.id)
    categorias = []
    for cat in categoria_crud.list_categorias(
        db, estab.id, apenas_ativas=True
    ):
        itens = [p for p in produtos if p.id_categoria == cat.id]
        if itens:
            dados = CategoriaResponse.model_validate(cat).model_dump()
            categorias.append({**dados, 'produtos': itens})
    return {
        'estabelecimento': estab,
        'mesa_numero': mesa_numero,
        'categorias': categorias,
    }


@router.post(
    '/{slug}/pedidos',
    response_model=PedidoEnviado,
    status_code=status.HTTP_201_CREATED,
)
def enviar_pedido(slug: str, data: PedidoPublicoCreate, db: DbSession):
    estab = estabelecimento_crud.get_por_slug(db, slug)
    if data.mesa_token:
        mesa = mesa_crud.get_mesa_por_token(db, estab.id, data.mesa_token)
        sessao = pedido_crud.abrir_sessao_para_pedido(db, estab, mesa=mesa)
    else:
        if data.tipo == 'mesa':
            raise BusinessRuleError('Pedido de mesa exige o QR Code da mesa')
        sessao = pedido_crud.abrir_sessao_para_pedido(
            db, estab, tipo=data.tipo, cliente_nome=data.cliente_nome
        )
    pedido = pedido_crud.criar_pedido(
        db, estab, sessao, data.itens, data.observacao, origem='cliente'
    )
    return PedidoEnviado(
        numero=pedido.id, codigo_acompanhamento=pedido.codigo_acompanhamento
    )


@router.get('/pedidos/{codigo}', response_model=PedidoAcompanhamento)
def acompanhar(codigo: str, db: DbSession):
    pedido = pedido_crud.get_por_codigo(db, codigo)
    dados = pedido_crud.pedido_to_dict(pedido, pedido.estabelecimento)
    return {
        **dados,
        'numero': pedido.id,
        'nome_loja': pedido.estabelecimento.nome_loja,
        'itens': [
            {
                'nome_produto': i['nome_produto'],
                'quantidade': i['quantidade'],
                'status': i['status'],
            }
            for i in dados['itens']
        ],
    }
