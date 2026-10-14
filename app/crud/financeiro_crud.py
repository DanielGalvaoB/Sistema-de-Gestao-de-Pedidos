from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.errors import BusinessRuleError, ConflictError, NotFoundError
from app.core.utils import q2, utcnow
from app.models.models import CategoriaFinanceira, MovimentacaoFinanceira


def _to_utc_naive(dt: datetime | None) -> datetime:
    if dt is None:
        return utcnow()
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


# ----- Categorias financeiras -----
def list_categorias(db: Session, id_estab: int):
    # Categorias de saida antigas ficam guardadas, mas nao sao mais usadas
    q = select(CategoriaFinanceira).where(
        CategoriaFinanceira.id_estabelecimento == id_estab,
        CategoriaFinanceira.tipo == 'entrada',
    )
    return db.scalars(q.order_by(CategoriaFinanceira.nome)).all()


def get_categoria(db: Session, id_estab: int, cat_id: int):
    cat = db.get(CategoriaFinanceira, cat_id)
    if not cat or cat.id_estabelecimento != id_estab:
        raise NotFoundError('Categoria financeira nao encontrada')
    return cat


def _nome_livre(db, id_estab, nome, tipo, exceto=0):
    if db.scalar(
        select(CategoriaFinanceira.id).where(
            CategoriaFinanceira.id_estabelecimento == id_estab,
            CategoriaFinanceira.tipo == tipo,
            func.lower(CategoriaFinanceira.nome) == nome.lower(),
            CategoriaFinanceira.id != exceto,
        )
    ):
        raise ConflictError('Ja existe uma categoria com este nome')


def create_categoria(db: Session, id_estab: int, data):
    _nome_livre(db, id_estab, data.nome, data.tipo)
    cat = CategoriaFinanceira(
        id_estabelecimento=id_estab, nome=data.nome, tipo=data.tipo
    )
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


def update_categoria(db: Session, id_estab: int, cat_id: int, data):
    cat = get_categoria(db, id_estab, cat_id)
    if cat.sistema:
        raise BusinessRuleError('Categorias do sistema nao podem ser editadas')
    upd = data.model_dump(exclude_unset=True, exclude_none=True)
    if 'nome' in upd:
        _nome_livre(db, id_estab, upd['nome'], cat.tipo, exceto=cat.id)
    for k, v in upd.items():
        setattr(cat, k, v)
    db.commit()
    db.refresh(cat)
    return cat


# ----- Movimentacoes -----
def mov_to_dict(m: MovimentacaoFinanceira) -> dict:
    return {
        'id': m.id,
        'tipo': m.tipo,
        'descricao': m.descricao,
        'id_categoria': m.id_categoria,
        'categoria_nome': m.categoria.nome,
        'valor': m.valor,
        'data_hora': m.data_hora,
        'metodo_pagamento': m.metodo_pagamento,
        'observacao': m.observacao,
        'id_pagamento': m.id_pagamento,
        'status': m.status,
        'cancelado_em': m.cancelado_em,
        'motivo_cancelamento': m.motivo_cancelamento,
        'automatica': m.id_pagamento is not None,
    }


def _validar_categoria(db, id_estab, cat_id, tipo):
    cat = get_categoria(db, id_estab, cat_id)
    if cat.tipo != tipo:
        raise BusinessRuleError(
            'Categoria nao corresponde ao tipo do lancamento'
        )
    if not cat.ativo:
        raise BusinessRuleError('Categoria financeira desativada')
    if cat.sistema:
        raise BusinessRuleError(
            'A categoria "Vendas" e alimentada automaticamente pelos '
            'pagamentos; use "Outras receitas" para entradas manuais'
        )
    return cat


def create_movimentacao(db: Session, id_estab: int, data, user_id: int):
    _validar_categoria(db, id_estab, data.id_categoria, data.tipo)
    mov = MovimentacaoFinanceira(
        id_estabelecimento=id_estab,
        tipo=data.tipo,
        descricao=data.descricao,
        id_categoria=data.id_categoria,
        valor=q2(data.valor),
        data_hora=_to_utc_naive(data.data_hora),
        metodo_pagamento=data.metodo_pagamento,
        observacao=data.observacao,
        id_usuario=user_id,
        status='ativa',
    )
    db.add(mov)
    db.commit()
    return get_movimentacao(db, id_estab, mov.id)


def get_movimentacao(db: Session, id_estab: int, mov_id: int):
    mov = db.scalar(
        select(MovimentacaoFinanceira)
        .options(selectinload(MovimentacaoFinanceira.categoria))
        .where(
            MovimentacaoFinanceira.id == mov_id,
            MovimentacaoFinanceira.id_estabelecimento == id_estab,
        )
    )
    if not mov:
        raise NotFoundError('Movimentacao nao encontrada')
    return mov


def update_movimentacao(db: Session, id_estab: int, mov_id: int, data):
    mov = get_movimentacao(db, id_estab, mov_id)
    if mov.status != 'ativa':
        raise BusinessRuleError('Lancamento cancelado nao pode ser editado')
    if mov.id_pagamento is not None:
        raise BusinessRuleError(
            'Lancamentos gerados por pagamentos so podem ser alterados '
            'pelo estorno do pagamento'
        )
    upd = data.model_dump(exclude_unset=True, exclude_none=True)
    if 'id_categoria' in upd:
        _validar_categoria(db, id_estab, upd['id_categoria'], mov.tipo)
    if 'valor' in upd:
        upd['valor'] = q2(upd['valor'])
    if 'data_hora' in upd:
        upd['data_hora'] = _to_utc_naive(upd['data_hora'])
    for k, v in upd.items():
        setattr(mov, k, v)
    db.commit()
    return get_movimentacao(db, id_estab, mov_id)


def cancelar_movimentacao(db: Session, id_estab, mov_id, motivo, user_id):
    mov = get_movimentacao(db, id_estab, mov_id)
    if mov.status == 'cancelada':
        raise BusinessRuleError('Lancamento ja cancelado')
    if mov.id_pagamento is not None:
        raise BusinessRuleError(
            'Este lancamento veio de um pagamento; estorne o pagamento'
        )
    mov.status = 'cancelada'
    mov.cancelado_em = utcnow()
    mov.motivo_cancelamento = motivo
    mov.id_usuario_cancelamento = user_id
    db.commit()
    return get_movimentacao(db, id_estab, mov_id)


def list_movimentacoes(
    db: Session,
    id_estab: int,
    inicio: datetime | None = None,
    fim: datetime | None = None,
    id_categoria: int | None = None,
    metodo: str | None = None,
    status: str | None = None,
):
    q = (
        select(MovimentacaoFinanceira)
        .options(selectinload(MovimentacaoFinanceira.categoria))
        .where(
            MovimentacaoFinanceira.id_estabelecimento == id_estab,
            MovimentacaoFinanceira.tipo == 'entrada',
        )
    )
    if inicio:
        q = q.where(MovimentacaoFinanceira.data_hora >= inicio)
    if fim:
        q = q.where(MovimentacaoFinanceira.data_hora < fim)
    if id_categoria:
        q = q.where(MovimentacaoFinanceira.id_categoria == id_categoria)
    if metodo:
        q = q.where(MovimentacaoFinanceira.metodo_pagamento == metodo)
    if status:
        q = q.where(MovimentacaoFinanceira.status == status)
    return db.scalars(
        q.order_by(MovimentacaoFinanceira.data_hora.desc())
    ).all()
