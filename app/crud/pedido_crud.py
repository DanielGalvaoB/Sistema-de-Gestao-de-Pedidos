from app.models.models import ItemPedido, Menu, Pedido


def create_pedido(db, pedido):

    db_pedido = Pedido(id_estabelecimento=pedido.id_estabelecimento)

    db.add(db_pedido)
    db.commit()
    db.refresh(db_pedido)

    for item in pedido.itens:
        menu = db.query(Menu).filter(Menu.id == item.id_menu).first()

        subtotal = menu.preco * item.quantidade

        db_item = ItemPedido(
            id_pedido=db_pedido.id,
            id_menu=item.id_menu,
            quantidade=item.quantidade,
            subtotal=subtotal,
        )

        db.add(db_item)

    db.commit()

    return db_pedido
