# 🛠️ Código Pronto para Implementar

## Arquivo 1: Habilitar CORS no Backend

### Modificar: `app/app.py`

**Adicione no topo do arquivo:**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import categoria_router, menu_router, pedido_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title='PDV API')

# ✅ ADICIONE ESTO:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar: ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(categoria_router.router)
app.include_router(menu_router.router)
app.include_router(pedido_router.router)
```

---

## Arquivo 2: Completar CRUD do Menu

### Criar/Atualizar: `app/crud/menu_crud.py`

```python
from sqlalchemy import select
from app.models.models import Menu


def create_menu(db, menu):
    """Criar novo item de menu"""
    db_menu = Menu(
        nome=menu.nome,
        preco=menu.preco,
        descricao=menu.descricao,
        url_imagem=menu.url_imagem,
        id_categoria=menu.id_categoria,
        id_estabelecimento=menu.id_estabelecimento,
    )

    db.add(db_menu)
    db.commit()
    db.refresh(db_menu)

    return db_menu


def list_menu(db):
    """Listar todos os itens de menu"""
    return db.query(Menu).all()


def get_menu(db, menu_id: int):
    """Obter item de menu por ID"""
    return db.query(Menu).filter(Menu.id == menu_id).first()


def list_menu_by_categoria(db, categoria_id: int):
    """Listar itens de menu por categoria"""
    return db.query(Menu).filter(Menu.id_categoria == categoria_id).all()


def update_menu(db, menu_id: int, menu_update):
    """Atualizar item de menu"""
    menu = db.get(Menu, menu_id)
    if not menu:
        return None

    update_data = menu_update.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(menu, field, value)

    db.commit()
    db.refresh(menu)

    return menu


def delete_menu(db, menu_id: int):
    """Deletar item de menu"""
    menu = db.get(Menu, menu_id)
    if not menu:
        return None

    db.delete(menu)
    db.commit()

    return True
```

---

## Arquivo 3: Completar CRUD de Pedidos

### Criar/Atualizar: `app/crud/pedido_crud.py`

```python
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
```

---

## Arquivo 4: Atualizar Menu Router

### Criar/Atualizar: `app/routers/menu_router.py`

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud import menu_crud
from app.dependencies.db_dep import get_db
from app.schemas.menu_schema import MenuCreate, MenuUpdate, MenuResponse

router = APIRouter(prefix='/menu')


@router.post(
    path='/',
    status_code=status.HTTP_201_CREATED,
    response_model=MenuResponse,
)
def create_menu(menu: MenuCreate, db: Session = Depends(get_db)):
    """Criar novo item de menu"""
    return menu_crud.create_menu(db, menu)


@router.get(
    path='/',
    response_model=list[MenuResponse],
    status_code=status.HTTP_200_OK,
)
def list_menu(db: Session = Depends(get_db)):
    """Listar todos os itens de menu"""
    return menu_crud.list_menu(db)


@router.get(
    path='/{menu_id}',
    response_model=MenuResponse,
    status_code=status.HTTP_200_OK,
)
def get_menu(menu_id: int, db: Session = Depends(get_db)):
    """Obter item de menu específico"""
    menu = menu_crud.get_menu(db, menu_id)
    if not menu:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Item de menu não encontrado'
        )
    return menu


@router.put(
    path='/{menu_id}',
    response_model=MenuResponse,
    status_code=status.HTTP_200_OK,
)
def update_menu(
    menu_id: int,
    menu_update: MenuUpdate,
    db: Session = Depends(get_db)
):
    """Atualizar item de menu"""
    menu = menu_crud.update_menu(db, menu_id, menu_update)
    if not menu:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Item de menu não encontrado'
        )
    return menu


@router.delete(
    path='/{menu_id}',
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_menu(menu_id: int, db: Session = Depends(get_db)):
    """Deletar item de menu"""
    result = menu_crud.delete_menu(db, menu_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Item de menu não encontrado'
        )
    return None
```

---

## Arquivo 5: Atualizar Pedido Router

### Criar/Atualizar: `app/routers/pedido_router.py`

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud import pedido_crud
from app.dependencies.db_dep import get_db
from app.schemas.pedido_schema import PedidoCreate, PedidoResponse

router = APIRouter(prefix='/pedidos')


@router.post(
    path='/',
    status_code=status.HTTP_201_CREATED,
    response_model=PedidoResponse,
)
def create_pedido(pedido: PedidoCreate, db: Session = Depends(get_db)):
    """Criar novo pedido"""
    return pedido_crud.create_pedido(db, pedido)


@router.get(
    path='/',
    response_model=list[PedidoResponse],
    status_code=status.HTTP_200_OK,
)
def list_pedidos(db: Session = Depends(get_db)):
    """Listar todos os pedidos"""
    return pedido_crud.list_pedidos(db)


@router.get(
    path='/{pedido_id}',
    response_model=PedidoResponse,
    status_code=status.HTTP_200_OK,
)
def get_pedido(pedido_id: int, db: Session = Depends(get_db)):
    """Obter pedido específico"""
    pedido = pedido_crud.get_pedido(db, pedido_id)
    if not pedido:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Pedido não encontrado'
        )
    return pedido


@router.delete(
    path='/{pedido_id}',
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_pedido(pedido_id: int, db: Session = Depends(get_db)):
    """Deletar/cancelar um pedido"""
    result = pedido_crud.delete_pedido(db, pedido_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Pedido não encontrado'
        )
    return None
```

---

## Arquivo 6: Atualizar Menu Schema

### Criar/Atualizar: `app/schemas/menu_schema.py`

```python
from decimal import Decimal
from pydantic import BaseModel


class MenuCreate(BaseModel):
    nome: str
    preco: Decimal
    descricao: str | None = None
    url_imagem: str | None = None
    id_categoria: int
    id_estabelecimento: int


class MenuUpdate(BaseModel):
    nome: str | None = None
    preco: Decimal | None = None
    descricao: str | None = None
    url_imagem: str | None = None
    is_disponivel: bool | None = None


class MenuResponse(BaseModel):
    id: int
    nome: str
    preco: Decimal
    descricao: str | None = None
    url_imagem: str | None = None
    is_disponivel: bool

    class Config:
        orm_mode = True
```

---

## Arquivo 7: Atualizar Pedido Schema

### Criar/Atualizar: `app/schemas/pedido_schema.py`

```python
from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal


class ItemPedidoCreate(BaseModel):
    id_menu: int
    quantidade: int


class ItemPedidoResponse(BaseModel):
    id: int
    id_menu: int
    quantidade: int
    subtotal: Decimal

    class Config:
        orm_mode = True


class PedidoCreate(BaseModel):
    id_estabelecimento: int
    itens: list[ItemPedidoCreate]


class PedidoResponse(BaseModel):
    id: int
    id_estabelecimento: int
    created_at: datetime
    itens: list[ItemPedidoResponse] = []

    class Config:
        orm_mode = True
```

---

## Arquivo 8: Arquivo de Configuração da API (Frontend)

### Criar: `frontend/src/api/config.js`

```javascript
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

// Interceptor para tratamento de erros
api.interceptors.response.use(
  response => response,
  error => {
    console.error('❌ Erro na API:', {
      status: error.response?.status,
      message: error.response?.data?.detail || error.message,
      endpoint: error.config?.url,
    });
    return Promise.reject(error);
  }
);

export default api;
```

---

## Arquivo 9: Serviços API (Frontend)

### Criar: `frontend/src/api/categoriaAPI.js`

```javascript
import api from './config';

export const categoriaAPI = {
  async listar() {
    const response = await api.get('/categorias');
    return response.data;
  },

  async obter(id) {
    const response = await api.get(`/categorias/${id}`);
    return response.data;
  },

  async criar(dados) {
    const response = await api.post('/categorias', dados);
    return response.data;
  },

  async atualizar(id, dados) {
    const response = await api.put(`/categorias/${id}`, dados);
    return response.data;
  },

  async deletar(id) {
    await api.delete(`/categorias/${id}`);
    return true;
  },
};
```

### Criar: `frontend/src/api/menuAPI.js`

```javascript
import api from './config';

export const menuAPI = {
  async listar() {
    const response = await api.get('/menu');
    return response.data;
  },

  async obter(id) {
    const response = await api.get(`/menu/${id}`);
    return response.data;
  },

  async criar(dados) {
    const response = await api.post('/menu', dados);
    return response.data;
  },

  async atualizar(id, dados) {
    const response = await api.put(`/menu/${id}`, dados);
    return response.data;
  },

  async deletar(id) {
    await api.delete(`/menu/${id}`);
    return true;
  },
};
```

### Criar: `frontend/src/api/pedidoAPI.js`

```javascript
import api from './config';

export const pedidoAPI = {
  async listar() {
    const response = await api.get('/pedidos');
    return response.data;
  },

  async obter(id) {
    const response = await api.get(`/pedidos/${id}`);
    return response.data;
  },

  async criar(dados) {
    const response = await api.post('/pedidos', dados);
    return response.data;
  },

  async cancelar(id) {
    await api.delete(`/pedidos/${id}`);
    return true;
  },
};
```

---

## Arquivo 10: Hooks Customizados (Frontend)

### Criar: `frontend/src/hooks/useCategories.js`

```javascript
import { useState, useEffect } from 'react';
import { categoriaAPI } from '../api/categoriaAPI';

export function useCategories() {
  const [categorias, setCategorias] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const carregar = async () => {
    try {
      setLoading(true);
      const dados = await categoriaAPI.listar();
      setCategorias(dados);
      setError(null);
    } catch (erro) {
      setError(erro.message);
      console.error('Erro ao carregar categorias:', erro);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    carregar();
  }, []);

  return { categorias, loading, error, refetch: carregar };
}
```

### Criar: `frontend/src/hooks/useMenu.js`

```javascript
import { useState, useEffect } from 'react';
import { menuAPI } from '../api/menuAPI';

export function useMenu() {
  const [menu, setMenu] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const carregar = async () => {
    try {
      setLoading(true);
      const dados = await menuAPI.listar();
      setMenu(dados);
      setError(null);
    } catch (erro) {
      setError(erro.message);
      console.error('Erro ao carregar menu:', erro);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    carregar();
  }, []);

  return { menu, loading, error, refetch: carregar };
}
```

### Criar: `frontend/src/hooks/useCart.js`

```javascript
import { useState, useCallback } from 'react';

export function useCart() {
  const [carrinho, setCarrinho] = useState([]);

  const adicionarItem = useCallback((menu, quantidade = 1) => {
    setCarrinho(prev => {
      const existe = prev.find(item => item.id_menu === menu.id);

      if (existe) {
        return prev.map(item =>
          item.id_menu === menu.id
            ? { ...item, quantidade: item.quantidade + quantidade }
            : item
        );
      }

      return [
        ...prev,
        {
          id_menu: menu.id,
          quantidade,
          preco: parseFloat(menu.preco),
          nome: menu.nome,
        },
      ];
    });
  }, []);

  const removerItem = useCallback((menuId) => {
    setCarrinho(prev => prev.filter(item => item.id_menu !== menuId));
  }, []);

  const atualizarQuantidade = useCallback((menuId, quantidade) => {
    if (quantidade <= 0) {
      removerItem(menuId);
      return;
    }

    setCarrinho(prev =>
      prev.map(item =>
        item.id_menu === menuId ? { ...item, quantidade } : item
      )
    );
  }, [removerItem]);

  const limparCarrinho = useCallback(() => {
    setCarrinho([]);
  }, []);

  const calcularTotal = useCallback(() => {
    return carrinho.reduce((total, item) => {
      return total + item.preco * item.quantidade;
    }, 0);
  }, [carrinho]);

  return {
    carrinho,
    adicionarItem,
    removerItem,
    atualizarQuantidade,
    limparCarrinho,
    calcularTotal,
    quantidadeItens: carrinho.length,
  };
}
```

---

## Resumo dos Arquivos a Modificar/Criar

### Backend (Python) - 7 arquivos
- ✏️ `app/app.py` - Adicionar CORS
- ✏️ `app/crud/menu_crud.py` - Completar CRUD
- ✏️ `app/crud/pedido_crud.py` - Completar CRUD
- ✏️ `app/routers/menu_router.py` - Completar endpoints
- ✏️ `app/routers/pedido_router.py` - Completar endpoints
- ✏️ `app/schemas/menu_schema.py` - Adicionar MenuUpdate
- ✏️ `app/schemas/pedido_schema.py` - Adicionar response models

### Frontend (JavaScript) - 10 arquivos
- ✏️ `frontend/src/api/config.js` - Configuração Axios
- ✏️ `frontend/src/api/categoriaAPI.js` - Serviço de categorias
- ✏️ `frontend/src/api/menuAPI.js` - Serviço de menu
- ✏️ `frontend/src/api/pedidoAPI.js` - Serviço de pedidos
- ✏️ `frontend/src/hooks/useCategories.js` - Hook de categorias
- ✏️ `frontend/src/hooks/useMenu.js` - Hook de menu
- ✏️ `frontend/src/hooks/useCart.js` - Hook de carrinho

---

## 🚀 Como Implementar

1. **Backend (30 min)**
   ```bash
   # 1. Copiar o código dos arquivos acima nos arquivos respectivos
   # 2. Testar com curl/Postman
   ```

2. **Frontend (4-5 horas)**
   ```bash
   # 1. Criar projeto React
   npm create vite@latest pdv-frontend -- --template react
   cd pdv-frontend
   npm install
   
   # 2. Instalar dependências
   npm install axios react-router-dom
   
   # 3. Copiar serviços e hooks
   # 4. Copiar componentes (veja GUIA_FRONTEND.md)
   # 5. Testar no navegador
   ```

---

**Todos os códigos acima são prontos para usar e seguem as melhores práticas!** ✅
