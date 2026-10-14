"""Rotas publicas: cardapio digital, envio e acompanhamento de pedidos."""

from decimal import Decimal

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
from app.models.models import STATUS_SESSAO_ABERTA
from app.schemas.categoria_schema import CategoriaResponse
from app.schemas.estabelecimento_schema import EstabelecimentoPublico
from app.schemas.menu_schema import MenuResponse
from app.schemas.pedido_schema import (
    ContaAcompanhamento,
    PedidoAcompanhamento,
    PedidoPublicoCreate,
)

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
    mesa = None
    if data.mesa_token:
        mesa = mesa_crud.get_mesa_por_token(db, estab.id, data.mesa_token)
    origem = None
    if data.codigo_origem:
        origem = pedido_crud.get_por_codigo(db, data.codigo_origem)
        if origem.id_estabelecimento != estab.id:
            raise BusinessRuleError('Pedido de origem invalido')
    if origem is not None:
        sessao = pedido_crud.sessao_para_novo_pedido(db, estab, origem, mesa)
    elif mesa is not None:
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


def _acompanhamento(pedido) -> dict:
    dados = pedido_crud.pedido_to_dict(pedido, pedido.estabelecimento)
    return {
        **dados,
        'numero': pedido.id,
        'nome_loja': pedido.estabelecimento.nome_loja,
        'slug': pedido.estabelecimento.slug,
        'itens': [
            {
                'nome_produto': i['nome_produto'],
                'quantidade': i['quantidade'],
                'status': i['status'],
            }
            for i in dados['itens']
        ],
    }


@router.get('/pedidos/{codigo}', response_model=PedidoAcompanhamento)
def acompanhar(codigo: str, db: DbSession):
    return _acompanhamento(pedido_crud.get_por_codigo(db, codigo))


@router.get('/pedidos/{codigo}/conta', response_model=ContaAcompanhamento)
def acompanhar_conta(codigo: str, db: DbSession):
    """Todos os pedidos da mesma conta do pedido informado."""
    pedido = pedido_crud.get_por_codigo(db, codigo)
    sessao = pedido.sessao
    pedidos = pedido_crud.list_pedidos(
        db, pedido.id_estabelecimento, id_sessao=sessao.id
    )
    total = sum(
        (pedido_crud.total_pedido(p) for p in pedidos), start=Decimal('0')
    )
    return {
        'nome_loja': pedido.estabelecimento.nome_loja,
        'slug': pedido.estabelecimento.slug,
        'tipo_atendimento': sessao.tipo,
        'mesa_numero': sessao.mesa.numero if sessao.mesa else None,
        'conta_aberta': sessao.status in STATUS_SESSAO_ABERTA,
        'total': total,
        'pedidos': [_acompanhamento(p) for p in pedidos],
    }
