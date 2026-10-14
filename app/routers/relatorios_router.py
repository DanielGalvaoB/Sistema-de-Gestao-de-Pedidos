from datetime import date

from fastapi import APIRouter, Response

from app.core.errors import BusinessRuleError
from app.crud import relatorio_crud
from app.dependencies.auth_dep import DbSession, Financeiro
from app.schemas.financeiro_schema import RelatorioResumo

router = APIRouter(prefix='/relatorios', tags=['relatorios'])

PERIODO_MAXIMO_DIAS = 366


def _validar(inicio: date, fim: date):
    if fim < inicio:
        raise BusinessRuleError('Data final anterior a data inicial')
    if (fim - inicio).days > PERIODO_MAXIMO_DIAS:
        raise BusinessRuleError('Periodo maximo de 366 dias')


@router.get('/resumo', response_model=RelatorioResumo)
def resumo(
    inicio: date,
    fim: date,
    db: DbSession,
    user: Financeiro,
    metodo: str | None = None,
    id_categoria: int | None = None,
):
    _validar(inicio, fim)
    return relatorio_crud.resumo(
        db, user.id_estabelecimento, inicio, fim, metodo, id_categoria
    )


def _filtros(tipo, id_categoria, metodo, status_mov):
    return {
        'tipo': tipo,
        'id_categoria': id_categoria,
        'metodo': metodo,
        'status': status_mov,
    }


@router.get('/extrato.csv')
def extrato_csv(
    inicio: date,
    fim: date,
    db: DbSession,
    user: Financeiro,
    tipo: str | None = None,
    id_categoria: int | None = None,
    metodo: str | None = None,
    status_mov: str | None = None,
):
    _validar(inicio, fim)
    conteudo = relatorio_crud.extrato_csv(
        db,
        user.id_estabelecimento,
        inicio,
        fim,
        **_filtros(tipo, id_categoria, metodo, status_mov),
    )
    nome = f'extrato_{inicio}_{fim}.csv'
    return Response(
        content=conteudo.encode('utf-8'),
        media_type='text/csv; charset=utf-8',
        headers={'Content-Disposition': f'attachment; filename="{nome}"'},
    )


@router.get('/extrato.pdf')
def extrato_pdf(
    inicio: date,
    fim: date,
    db: DbSession,
    user: Financeiro,
    tipo: str | None = None,
    id_categoria: int | None = None,
    metodo: str | None = None,
    status_mov: str | None = None,
):
    _validar(inicio, fim)
    conteudo = relatorio_crud.extrato_pdf(
        db,
        user.id_estabelecimento,
        user.estabelecimento.nome_loja,
        inicio,
        fim,
        **_filtros(tipo, id_categoria, metodo, status_mov),
    )
    nome = f'extrato_{inicio}_{fim}.pdf'
    return Response(
        content=conteudo,
        media_type='application/pdf',
        headers={'Content-Disposition': f'attachment; filename="{nome}"'},
    )
