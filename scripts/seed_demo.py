"""Cria um estabelecimento de demonstracao para testes locais.

Uso (com o banco ja migrado):
    python -m scripts.seed_demo

Credenciais de DEMONSTRACAO (apenas para desenvolvimento local):
    admin@example.com      / demo12345  (Administrador)
    atendente@example.com   / demo12345  (Atendente)
    cozinha@example.com     / demo12345  (Cozinha)
    financeiro@example.com  / demo12345  (Financeiro)
"""

from decimal import Decimal

from sqlalchemy import select

from app.crud import (
    categoria_crud,
    estabelecimento_crud,
    menu_crud,
    mesa_crud,
    usuario_crud,
)
from app.database import SessionLocal
from app.models.models import Estabelecimento
from app.schemas.categoria_schema import CategoriaCreate
from app.schemas.estabelecimento_schema import EstabelecimentoCreate
from app.schemas.menu_schema import MenuCreate
from app.schemas.mesa_schema import MesaCreate
from app.schemas.usuario_schema import UsuarioCreate

SENHA = 'demo12345'

CARDAPIO = {
    'Lanches': [
        ('X-Burger', '25.90', 'Pao, hamburguer 150g, queijo e salada', 15),
        ('X-Bacon', '29.90', 'Hamburguer 150g, bacon crocante e cheddar', 15),
        ('Misto quente', '14.00', 'Presunto e queijo na chapa', 8),
    ],
    'Porcoes': [
        ('Batata frita', '22.00', 'Porcao de 400g', 12),
        ('Frango a passarinho', '38.00', 'Porcao de 500g', 20),
    ],
    'Bebidas': [
        ('Refrigerante lata', '6.50', None, 1),
        ('Suco natural', '9.00', 'Laranja, limao ou abacaxi', 5),
        ('Agua mineral', '4.00', None, 1),
    ],
}


def main():
    with SessionLocal() as db:
        if db.scalar(
            select(Estabelecimento).where(
                Estabelecimento.email == 'admin@example.com'
            )
        ):
            print('Demo ja existe.')
            return
        est = estabelecimento_crud.create_estabelecimento(
            db,
            EstabelecimentoCreate(
                nome_loja='Lanchonete Demo',
                chave_pix='admin@example.com',
                nome_titular='Lanchonete Demo',
                cidade='SAO PAULO',
                email='admin@example.com',
                password=SENHA,
                nome_admin='Admin Demo',
            ),
        )
        for perfil in ('atendente', 'cozinha', 'financeiro'):
            usuario_crud.create_usuario(
                db,
                est.id,
                UsuarioCreate(
                    nome=perfil.capitalize(),
                    email=f'{perfil}@example.com',
                    password=SENHA,
                    perfil=perfil,
                ),
            )
        for ordem, (cat_nome, produtos) in enumerate(CARDAPIO.items()):
            cat = categoria_crud.create_categoria(
                db, est.id, CategoriaCreate(nome=cat_nome, ordem=ordem)
            )
            for nome, preco, desc, tempo in produtos:
                menu_crud.create_menu(
                    db,
                    est.id,
                    MenuCreate(
                        nome=nome,
                        preco=Decimal(preco),
                        descricao=desc,
                        id_categoria=cat.id,
                        tempo_preparo_min=tempo,
                    ),
                )
        for n in range(1, 7):
            mesa_crud.create_mesa(db, est.id, MesaCreate(numero=str(n)))
        print(f'Demo criada. Cardapio publico: /c/{est.slug}')


if __name__ == '__main__':
    main()
