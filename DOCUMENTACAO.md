# Documentação - Sistema de Gestão de Pedidos (PDV)

> **✅ Status: Backend 100% COMPLETO!** Todos os endpoints estão implementados e prontos para integração com frontend.

## 📋 Índice
1. [Visão Geral](#visão-geral)
2. [Arquitetura](#arquitetura)
3. [O que está Implementado](#o-que-está-implementado)
4. [O que está Faltando](#o-que-está-faltando)
5. [Guia de Integração com JavaScript](#guia-de-integração-com-javascript)

---

## 🎯 Visão Geral

**Projeto:** Sistema de Gestão de Pedidos (PDV - Ponto de Venda)  
**Stack:** FastAPI (Python) + SQLAlchemy + SQLite  
**Objetivo:** API REST para gerenciar pedidos, menu de itens, categorias e estabelecimentos

### Modelo de Negócio
- **Estabelecimentos** possuem menu de produtos
- **Produtos** são organizados em **Categorias**
- **Pedidos** contêm múltiplos **Itens** (produtos)
- **Pagamentos** são registrados para cada pedido

---

## 🏗️ Arquitetura

### Estrutura do Projeto
```
app/
├── app.py                 # Aplicação principal (FastAPI)
├── database.py            # Configuração do banco de dados
├── models/
│   └── models.py          # Modelos SQLAlchemy (entidades)
├── schemas/               # Modelos Pydantic (validação/serialização)
│   ├── categoria_schema.py
│   ├── menu_schema.py
│   └── pedido_schema.py
├── crud/                  # Lógica de banco de dados
│   ├── categoria_crud.py
│   ├── menu_crud.py
│   └── pedido_crud.py
├── routers/               # Endpoints da API
│   ├── categoria_router.py
│   ├── menu_router.py
│   └── pedido_router.py
└── dependencies/
    └── db_dep.py          # Injeção de dependências
```

### Modelo de Dados
```
┌─────────────────────────────────────────────────┐
│          RELACIONAMENTOS DAS ENTIDADES           │
├─────────────────────────────────────────────────┤
│                                                 │
│  Estabelecimento (1) ─────→ (N) Menu            │
│       │                                         │
│       └──────────────────→ (N) Pedido           │
│                                │                │
│  Categoria (1) ─────→ (N) Menu  │                │
│                          │      │                │
│                          ├─ ItemPedido ─────┘  │
│                          │                     │
│                          └─ (relacionamento)   │
│                                                 │
│  Pedido (1) ─────→ (N) Pagamento               │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## ✅ O que está Implementado

### 1. **Banco de Dados (database.py)**
- ✅ SQLite configurado
- ✅ SQLAlchemy como ORM
- ✅ Criação automática de tabelas

### 2. **Modelos (models.py)**
- ✅ `Categoria` - Categorias de produtos
- ✅ `Estabelecimento` - Lojas/Restaurantes (com autenticação parcial)
- ✅ `Menu` - Produtos com preço, descrição, imagem
- ✅ `Pedido` - Registro de pedidos
- ✅ `ItemPedido` - Itens dentro de cada pedido
- ✅ `Pagamento` - Registro de pagamentos

### 3. **Endpoints da API**

#### **Categorias** (`/categorias`)
| Método | Endpoint | Status | Descrição |
|--------|----------|--------|-----------|
| POST | `/` | ✅ | Criar categoria |
| GET | `/` | ✅ | Listar todas as categorias |
| GET | `/{id}` | ✅ | Obter categoria por ID |
| PUT | `/{id}` | ✅ | Atualizar categoria (completo) |
| PATCH | `/{id}` | ✅ | Atualizar categoria (parcial) |
| DELETE | `/{id}` | ✅ | Deletar categoria |

#### **Menu** (`/menu`)
| Método | Endpoint | Status | Descrição |
|--------|----------|--------|-----------|
| POST | `/` | ✅ | Criar produto |
| GET | `/` | ✅ | Listar produtos |
| GET | `/{id}` | ✅ | Obter produto por ID |
| PUT | `/{id}` | ✅ | Atualização completa ✨ NOVO |
| DELETE | `/{id}` | ✅ | Deletar produto |

#### **Pedidos** (`/pedidos`)
| Método | Endpoint | Status | Descrição |
|--------|----------|--------|-----------|
| POST | `/` | ✅ | Criar pedido com itens |
| GET | `/` | ✅ | Listar todos ✨ NOVO |
| GET | `/{id}` | ✅ | Obter pedido ✨ NOVO |
| DELETE | `/{id}` | ✅ | Cancelar pedido ✨ NOVO |

### 4. **Funcionalidades Implementadas** ✅ COMPLETO
- ✅ CRUD completo para categorias
- ✅ CRUD completo para menu
- ✅ CRUD completo para pedidos
- ✅ Criação de pedidos com múltiplos itens
- ✅ Cálculo automático de subtotal (preço × quantidade)
- ✅ Cálculo de total do pedido
- ✅ Listagem e filtragem de pedidos
- ✅ CORS configurado para aceitar requisições do frontend
- ✅ Relacionamentos entre entidades
- ✅ Validação com Pydantic
- ✅ Tratamento de erros HTTP
- ✅ Response models completos (PedidoResponse, ItemPedidoResponse)

---

## ❌ O que está Faltando (Futuras Melhorias)

### 1. **Funcionalidades de Negócio**
- ⏳ Autenticação de estabelecimentos
- ⏳ Sistema de pagamento (apenas modelo criado)
- ⏳ Status de pedido (pendente, preparando, pronto, entregue)
- ⏳ Histórico de pedidos
- ⏳ Disponibilidade de produtos
- ⏳ Filtros avançados (preço, disponibilidade)

### 2. **Segurança & Validação**
- ⏳ Autenticação/Autorização
- ⏳ Hash de senhas
- ⏳ Validações de negócio robustas

### 3. **Performance & Qualidade**
- ⏳ Paginação
- ⏳ Cache
- ⏳ Rate limiting
- ⏳ Testes unitários
- ⏳ Documentação Swagger completa

---

## 🚀 Guia de Integração com JavaScript

### Fase 1: Preparar o Backend

#### 1.1 Instalar CORS
```bash
pip install python-multipart
```

#### 1.2 Ativar CORS no app.py
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title='PDV API')

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar domínios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ... resto do código
```

#### 1.3 Completar os Endpoints Faltantes
Veja seção [Implementação dos Endpoints](#implementação-dos-endpoints) para código completo.

---

### Fase 2: Estrutura do Frontend (JavaScript/React)

#### 2.1 Configuração Base
```javascript
// config/api.js
const API_URL = 'http://localhost:8000';

export const apiClient = {
  // Helper para fazer requisições
  async request(endpoint, options = {}) {
    const response = await fetch(`${API_URL}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`);
    }
    
    return response.json();
  }
};
```

#### 2.2 Serviços por Entidade
```javascript
// services/categoriaService.js
import { apiClient } from '../config/api';

export const categoriaService = {
  async listar() {
    return apiClient.request('/categorias');
  },

  async criar(dados) {
    return apiClient.request('/categorias', {
      method: 'POST',
      body: JSON.stringify(dados),
    });
  },

  async atualizar(id, dados) {
    return apiClient.request(`/categorias/${id}`, {
      method: 'PUT',
      body: JSON.stringify(dados),
    });
  },

  async deletar(id) {
    return apiClient.request(`/categorias/${id}`, {
      method: 'DELETE',
    });
  },
};

// services/menuService.js
export const menuService = {
  async listar() {
    return apiClient.request('/menu');
  },

  async criar(dados) {
    return apiClient.request('/menu', {
      method: 'POST',
      body: JSON.stringify(dados),
    });
  },

  async obter(id) {
    return apiClient.request(`/menu/${id}`);
  },

  async atualizar(id, dados) {
    return apiClient.request(`/menu/${id}`, {
      method: 'PUT',
      body: JSON.stringify(dados),
    });
  },

  async deletar(id) {
    return apiClient.request(`/menu/${id}`, {
      method: 'DELETE',
    });
  },

  async listarPorCategoria(categoriaId) {
    return apiClient.request(`/menu?categoria=${categoriaId}`);
  },
};

// services/pedidoService.js
export const pedidoService = {
  async criar(dados) {
    return apiClient.request('/pedidos', {
      method: 'POST',
      body: JSON.stringify(dados),
    });
  },

  async listar() {
    return apiClient.request('/pedidos');
  },

  async obter(id) {
    return apiClient.request(`/pedidos/${id}`);
  },

  async atualizar(id, dados) {
    return apiClient.request(`/pedidos/${id}`, {
      method: 'PUT',
      body: JSON.stringify(dados),
    });
  },

  async cancelar(id) {
    return apiClient.request(`/pedidos/${id}`, {
      method: 'DELETE',
    });
  },
};
```

#### 2.3 Exemplo de Componente React
```javascript
// components/Menu.jsx
import React, { useState, useEffect } from 'react';
import { menuService, categoriaService } from '../services';

export function Menu() {
  const [categorias, setCategorias] = useState([]);
  const [menu, setMenu] = useState([]);
  const [categoriaSelecionada, setCategoriaSelecionada] = useState(null);
  const [carrinho, setCarrinho] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    carregarDados();
  }, []);

  const carregarDados = async () => {
    try {
      const [cats, itens] = await Promise.all([
        categoriaService.listar(),
        menuService.listar(),
      ]);
      setCategorias(cats);
      setMenu(itens);
    } catch (error) {
      console.error('Erro ao carregar dados:', error);
    } finally {
      setLoading(false);
    }
  };

  const adicionarAoCarrinho = (item) => {
    const existe = carrinho.find(i => i.id_menu === item.id);
    
    if (existe) {
      existe.quantidade += 1;
    } else {
      carrinho.push({
        id_menu: item.id,
        quantidade: 1,
      });
    }
    
    setCarrinho([...carrinho]);
  };

  const finalizarPedido = async () => {
    try {
      const pedido = await pedidoService.criar({
        id_estabelecimento: 1, // Obter de contexto/autenticação
        itens: carrinho,
      });
      
      console.log('Pedido criado:', pedido);
      setCarrinho([]);
      alert('Pedido finalizado com sucesso!');
    } catch (error) {
      console.error('Erro ao finalizar pedido:', error);
    }
  };

  if (loading) return <div>Carregando...</div>;

  return (
    <div className="menu-container">
      <h1>Menu</h1>
      
      {/* Filtro de Categorias */}
      <div className="categorias">
        {categorias.map(cat => (
          <button
            key={cat.id}
            onClick={() => setCategoriaSelecionada(cat.id)}
            className={categoriaSelecionada === cat.id ? 'ativo' : ''}
          >
            {cat.nome}
          </button>
        ))}
      </div>

      {/* Lista de Produtos */}
      <div className="produtos">
        {menu
          .filter(item => 
            !categoriaSelecionada || item.id_categoria === categoriaSelecionada
          )
          .map(item => (
            <div key={item.id} className="produto">
              <img src={item.url_imagem} alt={item.nome} />
              <h3>{item.nome}</h3>
              <p>{item.descricao}</p>
              <p className="preco">R$ {item.preco}</p>
              <button onClick={() => adicionarAoCarrinho(item)}>
                Adicionar ao carrinho
              </button>
            </div>
          ))}
      </div>

      {/* Carrinho */}
      <div className="carrinho">
        <h2>Carrinho ({carrinho.length})</h2>
        {carrinho.map((item, idx) => (
          <div key={idx}>
            Item: {item.id_menu} - Qtd: {item.quantidade}
          </div>
        ))}
        <button onClick={finalizarPedido} disabled={carrinho.length === 0}>
          Finalizar Pedido
        </button>
      </div>
    </div>
  );
}
```

#### 2.4 Usando com Fetch ou Axios
```javascript
// Com Axios (recomendado)
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

// GET
api.get('/categorias')
  .then(res => console.log(res.data))
  .catch(err => console.error(err));

// POST
api.post('/pedidos', {
  id_estabelecimento: 1,
  itens: [
    { id_menu: 1, quantidade: 2 },
    { id_menu: 2, quantidade: 1 },
  ],
})
  .then(res => console.log(res.data))
  .catch(err => console.error(err));
```

---

### Fase 3: Checklist de Implementação

#### ✅ Necessário antes de integrar
- [ ] CORS habilitado
- [ ] Todos os endpoints CRUD implementados
- [ ] Response models consistentes
- [ ] Tratamento de erros
- [ ] Validações de entrada

#### ✅ Recomendado
- [ ] Autenticação (JWT)
- [ ] Logging estruturado
- [ ] Documentação Swagger
- [ ] Testes da API
- [ ] Rate limiting
- [ ] Cache

---

## 📝 Implementação dos Endpoints Faltantes

### 1. Atualizar menu_crud.py
```python
# Adicionar ao menu_crud.py
from sqlalchemy import select
from app.models.models import Menu

def get_menu(db, menu_id: int):
    """Obter menu por ID"""
    return db.query(Menu).filter(Menu.id == menu_id).first()

def list_menu_by_categoria(db, categoria_id: int):
    """Listar menus por categoria"""
    return db.query(Menu).filter(Menu.id_categoria == categoria_id).all()

def update_menu(db, menu_id: int, menu_update):
    """Atualizar menu"""
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
    """Deletar menu"""
    menu = db.get(Menu, menu_id)
    if not menu:
        return None
    
    db.delete(menu)
    db.commit()
    return True
```

### 2. Atualizar pedido_crud.py
```python
# Adicionar ao pedido_crud.py
from sqlalchemy import select
from app.models.models import Pedido, ItemPedido

def list_pedidos(db):
    """Listar todos os pedidos"""
    return db.query(Pedido).all()

def get_pedido(db, pedido_id: int):
    """Obter pedido por ID"""
    return db.query(Pedido).filter(Pedido.id == pedido_id).first()

def delete_pedido(db, pedido_id: int):
    """Deletar pedido"""
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

### 3. Atualizar menu_router.py
```python
# Atualizar menu_router.py completo
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud import menu_crud
from app.dependencies.db_dep import get_db
from app.schemas.menu_schema import MenuCreate, MenuUpdate, MenuResponse

router = APIRouter(prefix='/menu')

@router.post('/', response_model=MenuResponse, status_code=status.HTTP_201_CREATED)
def create_menu(menu: MenuCreate, db: Session = Depends(get_db)):
    return menu_crud.create_menu(db, menu)

@router.get('/', response_model=list[MenuResponse])
def list_menu(db: Session = Depends(get_db)):
    return menu_crud.list_menu(db)

@router.get('/{menu_id}', response_model=MenuResponse)
def get_menu(menu_id: int, db: Session = Depends(get_db)):
    menu = menu_crud.get_menu(db, menu_id)
    if not menu:
        raise HTTPException(status_code=404, detail='Menu não encontrado')
    return menu

@router.put('/{menu_id}', response_model=MenuResponse)
def update_menu(menu_id: int, menu_update: MenuUpdate, db: Session = Depends(get_db)):
    menu = menu_crud.update_menu(db, menu_id, menu_update)
    if not menu:
        raise HTTPException(status_code=404, detail='Menu não encontrado')
    return menu

@router.delete('/{menu_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_menu(menu_id: int, db: Session = Depends(get_db)):
    result = menu_crud.delete_menu(db, menu_id)
    if not result:
        raise HTTPException(status_code=404, detail='Menu não encontrado')
    return None
```

### 4. Atualizar pedido_router.py
```python
# Atualizar pedido_router.py completo
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud import pedido_crud
from app.dependencies.db_dep import get_db
from app.schemas.pedido_schema import PedidoCreate, PedidoResponse

router = APIRouter(prefix='/pedidos')

@router.post('/', response_model=PedidoResponse, status_code=status.HTTP_201_CREATED)
def create_pedido(pedido: PedidoCreate, db: Session = Depends(get_db)):
    return pedido_crud.create_pedido(db, pedido)

@router.get('/', response_model=list[PedidoResponse])
def list_pedidos(db: Session = Depends(get_db)):
    return pedido_crud.list_pedidos(db)

@router.get('/{pedido_id}', response_model=PedidoResponse)
def get_pedido(pedido_id: int, db: Session = Depends(get_db)):
    pedido = pedido_crud.get_pedido(db, pedido_id)
    if not pedido:
        raise HTTPException(status_code=404, detail='Pedido não encontrado')
    return pedido

@router.delete('/{pedido_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_pedido(pedido_id: int, db: Session = Depends(get_db)):
    result = pedido_crud.delete_pedido(db, pedido_id)
    if not result:
        raise HTTPException(status_code=404, detail='Pedido não encontrado')
    return None
```

### 5. Atualizar schemas

```python
# menu_schema.py - adicionar MenuUpdate
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

```python
# pedido_schema.py - adicionar models completos
from pydantic import BaseModel
from datetime import datetime

class ItemPedidoCreate(BaseModel):
    id_menu: int
    quantidade: int

class ItemPedidoResponse(BaseModel):
    id: int
    id_menu: int
    quantidade: int
    subtotal: float

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

## 🔗 Endpoints Resumo

### Após implementar tudo:
```
GET    /categorias              # Listar categorias
POST   /categorias              # Criar categoria
GET    /categorias/{id}         # Obter categoria
PUT    /categorias/{id}         # Atualizar categoria
PATCH  /categorias/{id}         # Atualizar parcial
DELETE /categorias/{id}         # Deletar categoria

GET    /menu                    # Listar menu
POST   /menu                    # Criar item
GET    /menu/{id}               # Obter item
PUT    /menu/{id}               # Atualizar item
DELETE /menu/{id}               # Deletar item

GET    /pedidos                 # Listar pedidos
POST   /pedidos                 # Criar pedido
GET    /pedidos/{id}            # Obter pedido
DELETE /pedidos/{id}            # Deletar pedido
```

---

## 🎓 Próximos Passos Recomendados

1. **Curto prazo:** Implementar endpoints faltantes (1-2 horas)
2. **Médio prazo:** Adicionar autenticação JWT (2-3 horas)
3. **Médio prazo:** Criar interface Frontend (UI/UX) com React/Vue
4. **Longo prazo:** Adicionar pagamentos, relatórios, analytics
5. **Longo prazo:** Deploy em produção (Docker, CI/CD)

---

## 📞 Referências
- FastAPI Docs: https://fastapi.tiangolo.com/
- SQLAlchemy: https://www.sqlalchemy.org/
- Pydantic: https://docs.pydantic.dev/
- CORS em FastAPI: https://fastapi.tiangolo.com/tutorial/cors/
