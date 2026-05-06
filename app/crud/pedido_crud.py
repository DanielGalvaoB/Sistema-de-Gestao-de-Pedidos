from app.models.models import ItemPedido, Menu, Pedido


def create_pedido(db, pedido):
    """Criar novo pedido"""
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


def list_pedidos(db):
    """Listar todos os pedidos"""
    return db.query(Pedido).all()


def get_pedido(db, pedido_id: int):
    """Obter pedido por ID"""
    return db.query(Pedido).filter(Pedido.id == pedido_id).first()


def delete_pedido(db, pedido_id: int):
    """Deletar/cancelar um pedido"""
    pedido = db.get(Pedido, pedido_id)
    if not pedido:
        return None

    db.delete(pedido)
    db.commit()

    return True


def get_total_pedido(db, pedido_id: int):
    """Calcular total do pedido"""
    itens = db.query(ItemPedido).filter(ItemPedido.id_pedido == pedido_id).all()
    total = sum(float(item.subtotal) for item in itens)
    return total
