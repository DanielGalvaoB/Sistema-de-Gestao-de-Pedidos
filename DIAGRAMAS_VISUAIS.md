# 📊 Diagramas Visuais - Sistema de Gestão de Pedidos

## 1. Fluxo de Dados (User Journey)

```
┌─────────────────────────────────────────────────────────────┐
│                    CLIENTE NO NAVEGADOR                     │
│                                                             │
│  1. Acessa http://localhost:3000                           │
│     ↓                                                       │
│  2. Vê categorias de produtos                              │
│     ↓                                                       │
│  3. Clica em "Bebidas"                                     │
│     ↓                                                       │
│  4. Vê produtos da categoria                               │
│     ↓                                                       │
│  5. Clica em "Adicionar ao carrinho"                       │
│     ↓                                                       │
│  6. Repete com mais produtos                               │
│     ↓                                                       │
│  7. Clica em "Finalizar Pedido"                            │
│     ↓                                                       │
│  8. Vê "Pedido criado com sucesso!"                        │
│     ↓                                                       │
│  9. Carrinho limpa, pronto para novo pedido                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Arquitetura em Camadas

```
┌────────────────────────────────────────────────────────────┐
│                     APRESENTAÇÃO                           │
│                   (React Components)                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │   Menu      │  │ Carrinho    │  │ Categorias  │       │
│  │ Component   │  │ Component   │  │ Component   │       │
│  └─────────────┘  └─────────────┘  └─────────────┘       │
└────────────────────────────────────────────────────────────┘
                           ↕
              HTTP GET/POST/PUT/DELETE
                      JSON/CORS
                           ↕
┌────────────────────────────────────────────────────────────┐
│                   APLICAÇÃO (API)                          │
│                   (FastAPI Routers)                        │
│  ┌──────────────────────────────────────────────┐         │
│  │ /categorias       /menu         /pedidos     │         │
│  │ GET, POST, PUT    GET, POST...   GET, POST...│         │
│  │ DELETE, PATCH                              │         │
│  └──────────────────────────────────────────────┘         │
└────────────────────────────────────────────────────────────┘
                           ↕
              SQLAlchemy ORM Queries
                           ↕
┌────────────────────────────────────────────────────────────┐
│                    BANCO DE DADOS                          │
│                    (SQLite Tables)                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    │
│  │Categoria │ │Menu      │ │Pedido    │ │Pagamento │    │
│  │ id       │ │ id       │ │ id       │ │ id       │    │
│  │ nome     │ │ nome     │ │ data     │ │ valor    │    │
│  │          │ │ preco    │ │ items[]  │ │ status   │    │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘    │
│                                                          │
└────────────────────────────────────────────────────────────┘
```

---

## 3. Fluxo de Requisição (GET Menu)

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│  CLIENTE REACT                                               │
│  ┌──────────────────────┐                                   │
│  │ useMenu()            │                                   │
│  │ fetch /menu          │                                   │
│  └──────────────────────┘                                   │
│           ↓ HTTP GET                                        │
│           │ http://localhost:8000/menu                     │
│           │                                                 │
│           ↓                                                 │
│  ┌──────────────────────────────────────────┐              │
│  │ FastAPI Router                           │              │
│  │ /menu (GET)                              │              │
│  │ ├─ Valida requisição                     │              │
│  │ ├─ Chama menu_crud.list_menu()           │              │
│  │ ├─ Formata resposta com MenuResponse     │              │
│  │ └─ Retorna JSON                          │              │
│  └──────────────────────────────────────────┘              │
│           ↓ JSON Response                                  │
│           │                                                 │
│           ↓                                                 │
│  ┌──────────────────────────────────────────┐              │
│  │ CRUD (menu_crud.py)                      │              │
│  │ list_menu(db)                            │              │
│  │ ├─ db.query(Menu)                        │              │
│  │ ├─ .all()                                │              │
│  │ └─ Retorna lista de menus                │              │
│  └──────────────────────────────────────────┘              │
│           ↓ SQL Query                                      │
│           │ SELECT * FROM menu                            │
│           │                                                 │
│           ↓                                                 │
│  ┌──────────────────────────────────────────┐              │
│  │ BANCO DE DADOS (SQLite)                  │              │
│  │ Tabela: menu                             │              │
│  │ ┌────────────────────────────────────┐   │              │
│  │ │ id │ nome    │ preco │ categoria   │   │              │
│  │ ├────────────────────────────────────┤   │              │
│  │ │ 1  │ Pizza   │ 50.00 │ 1           │   │              │
│  │ │ 2  │ Pasta   │ 40.00 │ 1           │   │              │
│  │ │ 3  │ Agua    │  5.00 │ 2           │   │              │
│  │ └────────────────────────────────────┘   │              │
│  └──────────────────────────────────────────┘              │
│           ↑ Retorna dados                                  │
│           │                                                 │
│           ↓ JSON Response                                  │
│  [                                                          │
│    {                                                        │
│      "id": 1,                                               │
│      "nome": "Pizza",                                       │
│      "preco": "50.00",                                      │
│      "is_disponivel": true                                 │
│    },                                                       │
│    ...                                                      │
│  ]                                                          │
│           ↓                                                 │
│  Cliente React renderiza a lista                           │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 4. Fluxo de Criação de Pedido (POST)

```
┌───────────────────────────────────────────────────────────────┐
│                    CLIENTE (React)                            │
│                                                               │
│  Carrinho: [                                                  │
│    { id_menu: 1, quantidade: 2 },                             │
│    { id_menu: 3, quantidade: 1 }                              │
│  ]                                                            │
│                                                               │
│  Clica: "Finalizar Pedido"                                    │
│           ↓                                                   │
│  pedidoAPI.criar({                                            │
│    id_estabelecimento: 1,                                     │
│    itens: [...]                                               │
│  })                                                           │
│           ↓                                                   │
│  POST /pedidos                                                │
│  JSON Body: {                                                 │
│    "id_estabelecimento": 1,                                   │
│    "itens": [                                                 │
│      {"id_menu": 1, "quantidade": 2},                         │
│      {"id_menu": 3, "quantidade": 1}                          │
│    ]                                                          │
│  }                                                            │
│                                                               │
└───────────────────────────────────────────────────────────────┘
                      ↓ HTTP POST
         http://localhost:8000/pedidos
                      ↓
┌───────────────────────────────────────────────────────────────┐
│                  SERVIDOR (FastAPI)                           │
│                                                               │
│  pedido_router.py:                                            │
│  @router.post('/')                                            │
│  def create_pedido(pedido: PedidoCreate, db):                 │
│    ├─ Valida PedidoCreate (Pydantic)                          │
│    ├─ Chama pedido_crud.create_pedido(db, pedido)             │
│    └─ Retorna PedidoResponse                                  │
│                                                               │
│  pedido_crud.py:                                              │
│  def create_pedido(db, pedido):                               │
│    1. Cria Pedido(id_estabelecimento=1)                       │
│    2. db.add(pedido)                                          │
│    3. db.commit()                                             │
│    4. Para cada item:                                         │
│       └─ Busca Menu por id_menu                              │
│       └─ Calcula subtotal = preco × quantidade               │
│       └─ Cria ItemPedido                                      │
│       └─ db.add(item)                                         │
│    5. db.commit()                                             │
│    6. return pedido com ID 42                                 │
│                                                               │
└───────────────────────────────────────────────────────────────┘
                      ↓ SQL INSERT
        INSERT INTO pedido (...) VALUES (...)
        INSERT INTO item_pedido (...) VALUES (...)
                      ↓
┌───────────────────────────────────────────────────────────────┐
│              BANCO DE DADOS (SQLite)                          │
│                                                               │
│  INSERT INTO pedido (id_estabelecimento, created_at)          │
│  VALUES (1, 2026-05-04 14:30:00)  →  ID: 42                   │
│                                                               │
│  INSERT INTO item_pedido (...) VALUES (...) → ID: 1           │
│  INSERT INTO item_pedido (...) VALUES (...) → ID: 2           │
│                                                               │
│  Resultado: Pedido 42 com 2 itens criado ✅                    │
│                                                               │
└───────────────────────────────────────────────────────────────┘
                      ↑ Retorna dados
              JSON Response (201 Created)
                      ↓
┌───────────────────────────────────────────────────────────────┐
│                  CLIENTE (React)                              │
│                                                               │
│  Resposta:                                                    │
│  {                                                            │
│    "id": 42,                                                  │
│    "id_estabelecimento": 1,                                   │
│    "created_at": "2026-05-04T14:30:00",                       │
│    "itens": [                                                 │
│      {"id": 1, "id_menu": 1, "quantidade": 2, ...},           │
│      {"id": 2, "id_menu": 3, "quantidade": 1, ...}            │
│    ]                                                          │
│  }                                                            │
│                                                               │
│  Frontend:                                                    │
│  ├─ Limpa carrinho                                            │
│  ├─ Mostra "Pedido #42 criado com sucesso!"                   │
│  └─ Pronto para novo pedido                                   │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

---

## 5. Estrutura do Banco de Dados

```
┌─────────────────────────────────────────────────────────────┐
│                    BANCO DE DADOS                           │
│                     (SQLite)                                │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ CATEGORIA                                            │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │ id (PK) │ nome                                       │   │
│  │ 1       │ Pizzas                                     │   │
│  │ 2       │ Bebidas                                    │   │
│  │ 3       │ Sobremesas                                 │   │
│  └──────────────────────────────────────────────────────┘   │
│         ▲                                                    │
│         │ 1                                                  │
│         │ para                                               │
│         │ N                                                  │
│         │                                                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ MENU                                                 │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │ id │ nome   │ preco │ categoria_id (FK)             │   │
│  │ 1  │ Pizza  │ 50    │ 1                             │   │
│  │ 2  │ Pasta  │ 40    │ 1                             │   │
│  │ 3  │ Agua   │  5    │ 2                             │   │
│  └──────────────────────────────────────────────────────┘   │
│         ▲                                                    │
│         │ 1                                                  │
│         │ para                                               │
│         │ N                                                  │
│         │                                                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ ITEM_PEDIDO                                          │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │ id │ pedido_id │ menu_id │ quantidade │ subtotal    │   │
│  │ 1  │ 42        │ 1       │ 2          │ 100         │   │
│  │ 2  │ 42        │ 3       │ 1          │ 5           │   │
│  └──────────────────────────────────────────────────────┘   │
│         ▲           ▲                                        │
│         │           │                                        │
│         └─┬─────────┘                                        │
│           │ N para N                                         │
│           │                                                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ PEDIDO                                               │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │ id │ estabelecimento_id │ created_at                 │   │
│  │ 42 │ 1                  │ 2026-05-04 14:30:00        │   │
│  └──────────────────────────────────────────────────────┘   │
│         ▲                                                    │
│         │ 1 para N                                           │
│         │                                                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ PAGAMENTO                                            │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │ id │ pedido_id │ valor │ status                      │   │
│  │ 1  │ 42        │ 105   │ pendente                    │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. Status dos Endpoints

```
┌──────────────────────────────────────────────────────────┐
│                    ENDPOINTS STATUS                      │
│                                                          │
│  /categorias                        ✅ COMPLETO         │
│  ├─ GET                             ✅ Implementado     │
│  ├─ POST                            ✅ Implementado     │
│  ├─ GET/{id}                        ✅ Implementado     │
│  ├─ PUT/{id}                        ✅ Implementado     │
│  ├─ PATCH/{id}                      ✅ Implementado     │
│  └─ DELETE/{id}                     ✅ Implementado     │
│                                                          │
│  /menu                              🟡 INCOMPLETO      │
│  ├─ GET                             ✅ Implementado     │
│  ├─ POST                            ✅ Implementado     │
│  ├─ GET/{id}                        ❌ FALTANDO        │
│  ├─ PUT/{id}                        ❌ FALTANDO        │
│  └─ DELETE/{id}                     ❌ FALTANDO        │
│                                                          │
│  /pedidos                           🟡 INCOMPLETO      │
│  ├─ GET                             ❌ FALTANDO        │
│  ├─ POST                            ✅ Implementado     │
│  ├─ GET/{id}                        ❌ FALTANDO        │
│  └─ DELETE/{id}                     ❌ FALTANDO        │
│                                                          │
│  Total: 15 endpoints                                    │
│  ✅ Implementados: 9 (60%)                              │
│  ❌ Faltando: 6 (40%)                                   │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## 7. Fluxo de Desenvolvimento Recomendado

```
HOJE - MANHÃ (1 hora)
     ↓
┌────────────────────────┐
│ 1. Habilitar CORS      │ → 15 min
│    (app.py)            │
└────────────────────────┘
     ↓
┌────────────────────────┐
│ 2. Completar Menu CRUD │ → 15 min
│    (menu_crud.py)      │
│    (menu_router.py)    │
│    (menu_schema.py)    │
└────────────────────────┘
     ↓
┌────────────────────────┐
│ 3. Completar Pedido    │ → 15 min
│    CRUD                │
│    (pedido_crud.py)    │
│    (pedido_router.py)  │
│    (pedido_schema.py)  │
└────────────────────────┘
     ↓
┌────────────────────────┐
│ 4. Testar com curl     │ → 15 min
└────────────────────────┘
     ↓
HOJE - TARDE (2 horas)
     ↓
┌────────────────────────┐
│ 5. Setup React         │ → 30 min
│    npm create vite     │
│    npm install axios   │
└────────────────────────┘
     ↓
┌────────────────────────┐
│ 6. Copiar Serviços     │ → 30 min
│    (API + Hooks)       │
└────────────────────────┘
     ↓
┌────────────────────────┐
│ 7. Criar Componentes   │ → 60 min
│    <Menu />            │
│    <Carrinho />        │
│    <App />             │
└────────────────────────┘
     ↓
┌────────────────────────┐
│ 8. Testar Integração   │ → 30 min
│    Frontend + Backend  │
└────────────────────────┘
     ↓
✅ PRONTO!

Tempo Total: ~3-4 horas
```

---

## 8. Comparação: Antes vs Depois

```
ANTES (Estado Atual)
├─ Backend 70% pronto
│  ├─ Categoria: ✅ Completo
│  ├─ Menu: 50% (falta GET/{id}, PUT, DELETE)
│  └─ Pedido: 20% (falta GET, GET/{id}, DELETE)
├─ Frontend 0% (não existe)
├─ CORS: ❌ Não habilitado
└─ Deploy: Não possível

         ↓ (após implementação)

DEPOIS (Após Documentação)
├─ Backend 100% pronto
│  ├─ Categoria: ✅ Completo
│  ├─ Menu: ✅ Completo
│  └─ Pedido: ✅ Completo
├─ Frontend 100% funcional (React)
│  ├─ Menu com filtro
│  ├─ Carrinho inteligente
│  └─ Integração com API
├─ CORS: ✅ Habilitado
├─ Segurança: Pronto para adicionar auth
└─ Deploy: Pronto (Docker + produção)
```

---

## 9. Mapa Conceitual

```
                        PDV API
                           │
           ┌───────────────┼───────────────┐
           │               │               │
      Categorias         Menu           Pedidos
           │               │               │
      ┌────┴────┐      ┌────┴────┐    ┌───┴────┐
      │          │      │         │    │        │
     GET      POST     GET      POST  POST    GET
     PUT      PATCH    PUT      DELETE DELETE
     DELETE           PATCH


      Clientes                       API
    (JavaScript)                (Python)
         │                          │
    React.js ──────────────→ FastAPI
         │    HTTP + CORS       │
    axios │                      │
    hooks │      ←─────────────┘
         │      JSON
    Store
```

---

**Estes diagramas ajudam a visualizar:
- ✅ Como tudo se conecta
- ✅ Fluxo de dados
- ✅ Estrutura do banco
- ✅ Status dos endpoints
- ✅ Cronograma de implementação**
