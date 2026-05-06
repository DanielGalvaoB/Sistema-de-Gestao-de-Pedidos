# 📍 Mapa de Implementação - Quick Reference

## 🎯 Objetivo: Integração Frontend com Backend

```
┌──────────────────────────────────────────────────────────────┐
│                    FRONTEND (React)                          │
│                                                              │
│  ┌─ Página Menu ────────────────────────────────────────┐   │
│  │ ┌──────────────── useMenu() ──────────────┐          │   │
│  │ │ GET /menu → [items] → render grid       │          │   │
│  │ ├──────────────── useCategories() ───────┐│          │   │
│  │ │ GET /categorias → [cats] → render btns ││          │   │
│  │ └──────────────────────────────────────────┘│          │   │
│  │                                            │          │   │
│  │  <Menu> ─ adicionarAoCarrinho ──────────→ <Carrinho>│   │
│  │           menuAPI.criar()                          │   │
│  │                                            │          │   │
│  │  <Carrinho>                               │          │   │
│  │   POST /pedidos → pedidoAPI.criar()      │          │   │
│  │   ↓                                        │          │   │
│  │   Pedido criado com sucesso!             │          │   │
│  └────────────────────────────────────────────┘          │   │
└──────────────────────────────────────────────────────────────┘
                           ↕ HTTP + CORS
┌──────────────────────────────────────────────────────────────┐
│                    BACKEND (FastAPI)                         │
│                                                              │
│  Router: /categorias ┐                                      │
│  ├─ GET                                                     │
│  ├─ POST                                                    │
│  ├─ GET/{id}                                               │
│  ├─ PUT/{id}                                               │
│  ├─ PATCH/{id}                                             │
│  └─ DELETE/{id}                                            │
│                                                              │
│  Router: /menu       ┐                                      │
│  ├─ GET              │─→ menu_crud.py                      │
│  ├─ POST             │                                      │
│  ├─ GET/{id} ⭐NEW                                        │
│  ├─ PUT/{id} ⭐NEW                                        │
│  └─ DELETE/{id} ⭐NEW                                    │
│                                                              │
│  Router: /pedidos    ┐                                      │
│  ├─ POST             │─→ pedido_crud.py                    │
│  ├─ GET ⭐NEW                                             │
│  ├─ GET/{id} ⭐NEW                                       │
│  └─ DELETE/{id} ⭐NEW                                   │
│                                                              │
│  Schemas: Pydantic models (validação)                      │
│                                                              │
│  Models: SQLAlchemy (banco de dados)                       │
└──────────────────────────────────────────────────────────────┘
                           ↕ ORM
┌──────────────────────────────────────────────────────────────┐
│                    BANCO DE DADOS (SQLite)                  │
│                                                              │
│  categoria, estabelecimento, menu, pedido, item_pedido...   │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## ✅ Checklist de Implementação (2-3 horas)

### ⏱️ Fase 1: Backend (1 hora)

- [ ] **Habilitar CORS** (5 min)
  - Local: `app/app.py`
  - Copiar: Seção "Arquivo 1" de `CODIGO_PRONTO.md`

- [ ] **Atualizar Menu CRUD** (15 min)
  - Local: `app/crud/menu_crud.py`
  - Copiar: Seção "Arquivo 2" de `CODIGO_PRONTO.md`
  - Adiciona: get, update, delete, list_by_categoria

- [ ] **Atualizar Pedido CRUD** (15 min)
  - Local: `app/crud/pedido_crud.py`
  - Copiar: Seção "Arquivo 3" de `CODIGO_PRONTO.md`
  - Adiciona: list, get, delete, calcular_total

- [ ] **Atualizar Menu Router** (10 min)
  - Local: `app/routers/menu_router.py`
  - Copiar: Seção "Arquivo 4" de `CODIGO_PRONTO.md`
  - Resultado: 5 endpoints funcionais

- [ ] **Atualizar Pedido Router** (10 min)
  - Local: `app/routers/pedido_router.py`
  - Copiar: Seção "Arquivo 5" de `CODIGO_PRONTO.md`
  - Resultado: 4 endpoints funcionais

- [ ] **Atualizar Schemas** (5 min)
  - Menu: Adicionar `MenuUpdate` (Seção "Arquivo 6")
  - Pedido: Adicionar response models (Seção "Arquivo 7")

- [ ] **Testar com curl ou Postman** (5 min)
  ```bash
  # Testar CORS
  curl -X GET http://localhost:8000/categorias
  
  # Testar novo endpoint
  curl -X GET http://localhost:8000/menu
  ```

### ⏱️ Fase 2: Frontend Setup (30 min)

- [ ] **Criar Projeto React** (10 min)
  ```bash
  npm create vite@latest pdv-frontend -- --template react
  cd pdv-frontend
  npm install
  npm install axios react-router-dom
  ```

- [ ] **Criar Estrutura de Pastas** (5 min)
  ```bash
  mkdir -p src/api src/components src/hooks src/pages src/styles
  ```

- [ ] **Copiar Serviços API** (5 min)
  - `src/api/config.js` → Seção "Arquivo 8"
  - `src/api/categoriaAPI.js` → Seção "Arquivo 9"
  - `src/api/menuAPI.js` → Seção "Arquivo 9"
  - `src/api/pedidoAPI.js` → Seção "Arquivo 9"

- [ ] **Copiar Hooks** (5 min)
  - `src/hooks/useCategories.js` → Seção "Arquivo 10"
  - `src/hooks/useMenu.js` → Seção "Arquivo 10"
  - `src/hooks/useCart.js` → Seção "Arquivo 10"

- [ ] **Copiar Componentes** (5 min)
  - Ver `GUIA_FRONTEND.md` seção 5
  - Criar `<Menu />`, `<Carrinho />`, `App.jsx`

### ⏱️ Fase 3: Testes & Integração (30 min)

- [ ] **Iniciar Backend**
  ```bash
  cd Sistema-de-Gestao-de-Pedidos
  source .venv/bin/activate
  fastapi dev app/app.py
  ```

- [ ] **Iniciar Frontend**
  ```bash
  cd pdv-frontend
  npm run dev
  ```

- [ ] **Testar no Navegador**
  - Abrir http://localhost:5173
  - Verificar se categorias carregam
  - Clicar em "Adicionar ao carrinho"
  - Finalizar pedido
  - Ver console para erros

- [ ] **Testar Endpoints**
  ```bash
  # GET - Listar categorias
  curl http://localhost:8000/categorias
  
  # POST - Criar categoria
  curl -X POST http://localhost:8000/categorias \
    -H "Content-Type: application/json" \
    -d '{"nome":"Bebidas"}'
  
  # GET - Listar menu
  curl http://localhost:8000/menu
  
  # POST - Criar pedido
  curl -X POST http://localhost:8000/pedidos \
    -H "Content-Type: application/json" \
    -d '{
      "id_estabelecimento": 1,
      "itens": [
        {"id_menu": 1, "quantidade": 2}
      ]
    }'
  ```

---

## 📋 Ordem de Implementação (Passo a Passo)

### HOJE - Manhã (1.5 horas)
1. Abrir `CODIGO_PRONTO.md`
2. Copiar código do "Arquivo 1" → `app/app.py` (CORS)
3. Copiar código do "Arquivo 2" → `app/crud/menu_crud.py`
4. Copiar código do "Arquivo 3" → `app/crud/pedido_crud.py`
5. Copiar código do "Arquivo 4" → `app/routers/menu_router.py`
6. Copiar código do "Arquivo 5" → `app/routers/pedido_router.py`
7. Copiar código do "Arquivo 6" → `app/schemas/menu_schema.py`
8. Copiar código do "Arquivo 7" → `app/schemas/pedido_schema.py`
9. Testar com `curl` ou Postman
10. ✅ Backend pronto!

### HOJE - Tarde (1-2 horas)
1. Criar novo projeto React
2. Instalar dependências
3. Copiar arquivos de `CODIGO_PRONTO.md` (Arquivos 8, 9, 10)
4. Copiar componentes de `GUIA_FRONTEND.md`
5. Iniciar servidor React
6. Testar no navegador

### Testes Básicos (30 min)
- [ ] GET /categorias retorna dados
- [ ] GET /menu retorna dados
- [ ] POST /pedidos cria pedido
- [ ] DELETE /pedidos/{id} deleta pedido
- [ ] Frontend lista categorias
- [ ] Frontend lista menu
- [ ] Adicionar ao carrinho funciona
- [ ] Finalizar pedido funciona

---

## 🔍 Verificação de Qualidade

Antes de considerar "pronto":

### Backend
- [ ] ✅ CORS habilitado
- [ ] ✅ Todos 15 endpoints funcionam
- [ ] ✅ Resposta JSON consistente
- [ ] ✅ Tratamento de erro 404
- [ ] ✅ Validação com Pydantic
- [ ] ✅ Sem erros no console Python

### Frontend
- [ ] ✅ Categorias carregam
- [ ] ✅ Menu carrega
- [ ] ✅ Adicionar ao carrinho funciona
- [ ] ✅ Remover do carrinho funciona
- [ ] ✅ Quantidade pode ser ajustada
- [ ] ✅ Total calcula corretamente
- [ ] ✅ Finalizar pedido funciona
- [ ] ✅ Sem erros no console JavaScript

---

## 🎨 Estilo CSS Mínimo

Se não quiser copiar todo CSS, use isso:

```css
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: sans-serif;
  background: #f5f5f5;
}

.app-content {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 2rem;
  padding: 2rem;
}

.produtos-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
}

.produto-card {
  border: 1px solid #ddd;
  padding: 1rem;
  border-radius: 4px;
  cursor: pointer;
  transition: box-shadow 0.3s;
}

.produto-card:hover {
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}

button {
  padding: 0.75rem 1rem;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

button:hover {
  background: #5568d3;
}

@media (max-width: 768px) {
  .app-content {
    grid-template-columns: 1fr;
  }
}
```

---

## 📞 Suporte Rápido

Se algo não funcionar:

1. **CORS Error?**
   - Verifique se `app.add_middleware(CORSMiddleware...)` está em `app/app.py`
   - Reinicie o servidor FastAPI

2. **404 Not Found?**
   - Verifique se o endpoint existe em `routers/`
   - Verifique a URL exata (maiúscula/minúscula)

3. **JSON Error?**
   - Verifique o console do navegador (F12)
   - Verifique logs do FastAPI

4. **Dados não aparecem?**
   - Abra Dev Tools (F12) → Network
   - Veja a requisição HTTP
   - Verifique resposta

---

## 🎓 Estrutura Final Completa

Após seguir tudo acima:

```
Sistema-de-Gestao-de-Pedidos/
├── DOCUMENTACAO.md          ✅ (você recebeu)
├── GUIA_FRONTEND.md         ✅ (você recebeu)
├── RESUMO_EXECUTIVO.md      ✅ (você recebeu)
├── CODIGO_PRONTO.md         ✅ (você recebeu)
├── ROTEIRO_IMPLEMENTACAO.md ✅ (este arquivo)
├── app/
│   ├── app.py               ✏️ (CORS adicionado)
│   ├── crud/
│   │   ├── menu_crud.py     ✏️ (completado)
│   │   └── pedido_crud.py   ✏️ (completado)
│   ├── routers/
│   │   ├── menu_router.py   ✏️ (completado)
│   │   └── pedido_router.py ✏️ (completado)
│   └── schemas/
│       ├── menu_schema.py   ✏️ (MenuUpdate adicionado)
│       └── pedido_schema.py ✏️ (respostas adicionadas)
│
└── pdv-frontend/
    ├── package.json
    ├── src/
    │   ├── api/
    │   │   ├── config.js
    │   │   ├── categoriaAPI.js
    │   │   ├── menuAPI.js
    │   │   └── pedidoAPI.js
    │   ├── hooks/
    │   │   ├── useCategories.js
    │   │   ├── useMenu.js
    │   │   └── useCart.js
    │   ├── components/
    │   │   ├── Menu.jsx
    │   │   ├── Carrinho.jsx
    │   │   └── App.jsx
    │   └── App.css
```

---

## 📊 Resumo de Tempo

| Tarefa | Tempo |
|--------|-------|
| CORS + Backend | 1 hora |
| Frontend Setup | 30 min |
| Componentes | 1 hora |
| Testes | 30 min |
| **TOTAL** | **~3 horas** |

---

**🎉 Após seguir este roteiro, você terá um sistema completo funcionando!**

Comece agora: `CODIGO_PRONTO.md` → Copie o código → Cole nos arquivos → Teste! ✅
