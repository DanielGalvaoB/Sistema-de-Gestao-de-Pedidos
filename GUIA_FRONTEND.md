# Guia Prático: Integração Frontend JavaScript com PDV API

## 🚀 Começando Rápido

### Passo 1: Estrutura do Projeto Frontend

```
frontend/
├── public/
│   └── index.html
├── src/
│   ├── api/
│   │   ├── config.js           # Configuração da API
│   │   ├── categoriaAPI.js     # Serviços de Categoria
│   │   ├── menuAPI.js          # Serviços de Menu
│   │   └── pedidoAPI.js        # Serviços de Pedido
│   ├── components/
│   │   ├── Menu.jsx
│   │   ├── Carrinho.jsx
│   │   ├── Categorias.jsx
│   │   └── Pedidos.jsx
│   ├── pages/
│   │   ├── Home.jsx
│   │   └── Admin.jsx
│   ├── hooks/
│   │   ├── useCategories.js
│   │   ├── useMenu.js
│   │   └── useCart.js
│   └── App.jsx
└── package.json
```

### Passo 2: Setup Inicial (5 minutos)

#### 2.1 Criar projeto React
```bash
npm create vite@latest pdv-frontend -- --template react
cd pdv-frontend
npm install axios react-router-dom
```

#### 2.2 Arquivo de configuração (src/api/config.js)
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
    console.error('Erro na API:', {
      status: error.response?.status,
      message: error.response?.data?.detail,
      endpoint: error.config?.url,
    });
    return Promise.reject(error);
  }
);

export default api;
```

---

## 📦 Serviços da API

### Passo 3: Implementar Serviços

#### 3.1 Categorias (src/api/categoriaAPI.js)
```javascript
import api from './config';

export const categoriaAPI = {
  // ✅ Listar todas as categorias
  async listar() {
    try {
      const response = await api.get('/categorias');
      return response.data;
    } catch (error) {
      console.error('Erro ao listar categorias:', error);
      throw error;
    }
  },

  // ✅ Obter categoria específica
  async obter(id) {
    try {
      const response = await api.get(`/categorias/${id}`);
      return response.data;
    } catch (error) {
      console.error(`Erro ao obter categoria ${id}:`, error);
      throw error;
    }
  },

  // ✅ Criar nova categoria
  async criar(dados) {
    try {
      const response = await api.post('/categorias', dados);
      return response.data;
    } catch (error) {
      console.error('Erro ao criar categoria:', error);
      throw error;
    }
  },

  // ✅ Atualizar categoria
  async atualizar(id, dados) {
    try {
      const response = await api.put(`/categorias/${id}`, dados);
      return response.data;
    } catch (error) {
      console.error(`Erro ao atualizar categoria ${id}:`, error);
      throw error;
    }
  },

  // ✅ Deletar categoria
  async deletar(id) {
    try {
      await api.delete(`/categorias/${id}`);
      return true;
    } catch (error) {
      console.error(`Erro ao deletar categoria ${id}:`, error);
      throw error;
    }
  },
};
```

#### 3.2 Menu (src/api/menuAPI.js)
```javascript
import api from './config';

export const menuAPI = {
  // ✅ Listar todos os itens
  async listar() {
    try {
      const response = await api.get('/menu');
      return response.data;
    } catch (error) {
      console.error('Erro ao listar menu:', error);
      throw error;
    }
  },

  // ✅ Obter item específico
  async obter(id) {
    try {
      const response = await api.get(`/menu/${id}`);
      return response.data;
    } catch (error) {
      console.error(`Erro ao obter item ${id}:`, error);
      throw error;
    }
  },

  // ✅ Criar novo item
  async criar(dados) {
    try {
      const response = await api.post('/menu', dados);
      return response.data;
    } catch (error) {
      console.error('Erro ao criar item:', error);
      throw error;
    }
  },

  // ✅ Atualizar item
  async atualizar(id, dados) {
    try {
      const response = await api.put(`/menu/${id}`, dados);
      return response.data;
    } catch (error) {
      console.error(`Erro ao atualizar item ${id}:`, error);
      throw error;
    }
  },

  // ✅ Deletar item
  async deletar(id) {
    try {
      await api.delete(`/menu/${id}`);
      return true;
    } catch (error) {
      console.error(`Erro ao deletar item ${id}:`, error);
      throw error;
    }
  },
};
```

#### 3.3 Pedidos (src/api/pedidoAPI.js)
```javascript
import api from './config';

export const pedidoAPI = {
  // ✅ Listar todos os pedidos
  async listar() {
    try {
      const response = await api.get('/pedidos');
      return response.data;
    } catch (error) {
      console.error('Erro ao listar pedidos:', error);
      throw error;
    }
  },

  // ✅ Obter pedido específico
  async obter(id) {
    try {
      const response = await api.get(`/pedidos/${id}`);
      return response.data;
    } catch (error) {
      console.error(`Erro ao obter pedido ${id}:`, error);
      throw error;
    }
  },

  // ✅ Criar novo pedido
  async criar(dados) {
    try {
      const response = await api.post('/pedidos', dados);
      return response.data;
    } catch (error) {
      console.error('Erro ao criar pedido:', error);
      throw error;
    }
  },

  // ✅ Cancelar pedido
  async cancelar(id) {
    try {
      await api.delete(`/pedidos/${id}`);
      return true;
    } catch (error) {
      console.error(`Erro ao cancelar pedido ${id}:`, error);
      throw error;
    }
  },
};
```

---

## 🎣 Hooks Customizados

### Passo 4: Criar Hooks Reutilizáveis

#### 4.1 useCategories (src/hooks/useCategories.js)
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

#### 4.2 useMenu (src/hooks/useMenu.js)
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

#### 4.3 useCart (src/hooks/useCart.js)
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
      
      return [...prev, { id_menu: menu.id, quantidade, preco: menu.preco }];
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
      return total + (item.preco * item.quantidade);
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

## 🎨 Componentes

### Passo 5: Implementar Componentes

#### 5.1 Componente Menu (src/components/Menu.jsx)
```javascript
import React, { useState } from 'react';
import { useMenu } from '../hooks/useMenu';
import { useCategories } from '../hooks/useCategories';
import '../styles/Menu.css';

export function Menu({ onAdicionarAoCarrinho }) {
  const { categorias } = useCategories();
  const { menu, loading } = useMenu();
  const [categoriaSelecionada, setCategoriaSelecionada] = useState(null);

  const menuFiltrado = categoriaSelecionada
    ? menu.filter(item => item.id_categoria === categoriaSelecionada)
    : menu;

  if (loading) return <div className="loading">Carregando menu...</div>;

  return (
    <div className="menu-container">
      <h1>🍽️ Menu</h1>

      {/* Filtro de Categorias */}
      <div className="categorias-filtro">
        <button
          className={!categoriaSelecionada ? 'ativo' : ''}
          onClick={() => setCategoriaSelecionada(null)}
        >
          Todos
        </button>
        {categorias.map(categoria => (
          <button
            key={categoria.id}
            className={categoriaSelecionada === categoria.id ? 'ativo' : ''}
            onClick={() => setCategoriaSelecionada(categoria.id)}
          >
            {categoria.nome}
          </button>
        ))}
      </div>

      {/* Grade de Produtos */}
      <div className="produtos-grid">
        {menuFiltrado.map(item => (
          <div key={item.id} className="produto-card">
            {item.url_imagem && (
              <img src={item.url_imagem} alt={item.nome} className="produto-imagem" />
            )}
            <h3>{item.nome}</h3>
            {item.descricao && <p className="descricao">{item.descricao}</p>}
            <p className="preco">R$ {parseFloat(item.preco).toFixed(2)}</p>
            <button
              className="btn-adicionar"
              onClick={() => onAdicionarAoCarrinho(item)}
              disabled={!item.is_disponivel}
            >
              {item.is_disponivel ? 'Adicionar' : 'Indisponível'}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
```

#### 5.2 Componente Carrinho (src/components/Carrinho.jsx)
```javascript
import React from 'react';
import { pedidoAPI } from '../api/pedidoAPI';
import '../styles/Carrinho.css';

export function Carrinho({ carrinho, onRemoverItem, onAtualizarQuantidade, onFinalizarPedido }) {
  const [processando, setProcessando] = React.useState(false);
  const [erro, setErro] = React.useState(null);

  const total = carrinho.reduce((sum, item) => {
    return sum + (item.preco * item.quantidade);
  }, 0);

  const handleFinalizarPedido = async () => {
    try {
      setProcessando(true);
      setErro(null);

      const pedidoData = {
        id_estabelecimento: 1, // Obter de contexto/localStorage
        itens: carrinho.map(item => ({
          id_menu: item.id_menu,
          quantidade: item.quantidade,
        })),
      };

      const pedido = await pedidoAPI.criar(pedidoData);
      
      onFinalizarPedido(pedido);
      alert('Pedido criado com sucesso! ID: ' + pedido.id);
    } catch (error) {
      setErro('Erro ao finalizar pedido: ' + error.message);
    } finally {
      setProcessando(false);
    }
  };

  return (
    <div className="carrinho-container">
      <h2>🛒 Carrinho ({carrinho.length} itens)</h2>

      {carrinho.length === 0 ? (
        <p className="carrinho-vazio">Carrinho vazio</p>
      ) : (
        <>
          <div className="itens-carrinho">
            {carrinho.map(item => (
              <div key={item.id_menu} className="item-carrinho">
                <div className="info-item">
                  <h4>{item.id_menu}</h4>
                  <p className="preco-unitario">R$ {item.preco.toFixed(2)}</p>
                </div>

                <div className="controles-quantidade">
                  <button
                    onClick={() => onAtualizarQuantidade(item.id_menu, item.quantidade - 1)}
                    className="btn-quantidade"
                  >
                    −
                  </button>
                  <span className="quantidade">{item.quantidade}</span>
                  <button
                    onClick={() => onAtualizarQuantidade(item.id_menu, item.quantidade + 1)}
                    className="btn-quantidade"
                  >
                    +
                  </button>
                </div>

                <p className="subtotal">
                  R$ {(item.preco * item.quantidade).toFixed(2)}
                </p>

                <button
                  onClick={() => onRemoverItem(item.id_menu)}
                  className="btn-remover"
                >
                  🗑️
                </button>
              </div>
            ))}
          </div>

          <div className="resumo-pedido">
            <div className="linha-total">
              <span>Total:</span>
              <strong>R$ {total.toFixed(2)}</strong>
            </div>

            {erro && <p className="erro">{erro}</p>}

            <button
              onClick={handleFinalizarPedido}
              className="btn-finalizar"
              disabled={processando || carrinho.length === 0}
            >
              {processando ? 'Processando...' : 'Finalizar Pedido'}
            </button>
          </div>
        </>
      )}
    </div>
  );
}
```

#### 5.3 App.jsx Principal
```javascript
import React from 'react';
import { Menu } from './components/Menu';
import { Carrinho } from './components/Carrinho';
import { useCart } from './hooks/useCart';
import './App.css';

function App() {
  const {
    carrinho,
    adicionarItem,
    removerItem,
    atualizarQuantidade,
    limparCarrinho,
  } = useCart();

  const handleFinalizarPedido = (pedido) => {
    console.log('Pedido finalizado:', pedido);
    limparCarrinho();
    // Redirecionar para página de sucesso ou confirmar
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>🍕 PDV - Ponto de Venda</h1>
      </header>

      <div className="app-content">
        <div className="menu-section">
          <Menu onAdicionarAoCarrinho={adicionarItem} />
        </div>

        <div className="carrinho-section">
          <Carrinho
            carrinho={carrinho}
            onRemoverItem={removerItem}
            onAtualizarQuantidade={atualizarQuantidade}
            onFinalizarPedido={handleFinalizarPedido}
          />
        </div>
      </div>
    </div>
  );
}

export default App;
```

---

## 🎨 Estilos CSS Básicos

### Passo 6: Adicionar Estilos (src/App.css)
```css
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  background: #f5f5f5;
}

.app {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.app-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 2rem;
  text-align: center;
}

.app-content {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 2rem;
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
}

/* Menu */
.menu-container {
  background: white;
  border-radius: 8px;
  padding: 2rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.categorias-filtro {
  display: flex;
  gap: 1rem;
  margin: 1.5rem 0;
  flex-wrap: wrap;
}

.categorias-filtro button {
  padding: 0.5rem 1rem;
  border: 2px solid #ddd;
  background: white;
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.3s;
}

.categorias-filtro button.ativo {
  background: #667eea;
  color: white;
  border-color: #667eea;
}

.produtos-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1.5rem;
  margin-top: 2rem;
}

.produto-card {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  overflow: hidden;
  transition: transform 0.3s, box-shadow 0.3s;
  cursor: pointer;
}

.produto-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
}

.produto-imagem {
  width: 100%;
  height: 150px;
  object-fit: cover;
}

.produto-card h3 {
  padding: 1rem;
  font-size: 1rem;
}

.descricao {
  padding: 0 1rem;
  color: #666;
  font-size: 0.875rem;
}

.preco {
  padding: 0 1rem;
  color: #667eea;
  font-weight: bold;
  font-size: 1.25rem;
}

.btn-adicionar {
  width: calc(100% - 2rem);
  margin: 1rem;
  padding: 0.75rem;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.3s;
}

.btn-adicionar:hover:not(:disabled) {
  background: #5568d3;
}

.btn-adicionar:disabled {
  background: #ccc;
  cursor: not-allowed;
}

/* Carrinho */
.carrinho-container {
  background: white;
  border-radius: 8px;
  padding: 2rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  height: fit-content;
  position: sticky;
  top: 20px;
}

.carrinho-vazio {
  text-align: center;
  color: #999;
  padding: 2rem;
}

.itens-carrinho {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  max-height: 400px;
  overflow-y: auto;
  margin-bottom: 1.5rem;
}

.item-carrinho {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: #f9f9f9;
  border-radius: 4px;
}

.info-item h4 {
  font-size: 0.9rem;
}

.controles-quantidade {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-quantidade {
  width: 24px;
  height: 24px;
  border: 1px solid #ddd;
  background: white;
  border-radius: 4px;
  cursor: pointer;
  font-weight: bold;
}

.quantidade {
  min-width: 30px;
  text-align: center;
}

.subtotal {
  flex: 1;
  text-align: right;
  font-weight: bold;
}

.btn-remover {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1.2rem;
}

.resumo-pedido {
  padding-top: 1rem;
  border-top: 2px solid #eee;
}

.linha-total {
  display: flex;
  justify-content: space-between;
  font-size: 1.25rem;
  margin-bottom: 1rem;
}

.btn-finalizar {
  width: 100%;
  padding: 1rem;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  font-weight: bold;
  cursor: pointer;
  transition: background 0.3s;
}

.btn-finalizar:hover:not(:disabled) {
  background: #5568d3;
}

.btn-finalizar:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.erro {
  color: #e74c3c;
  margin-bottom: 1rem;
  padding: 0.75rem;
  background: #fadbd8;
  border-radius: 4px;
}

/* Responsivo */
@media (max-width: 768px) {
  .app-content {
    grid-template-columns: 1fr;
  }

  .carrinho-section {
    position: relative;
    top: 0;
    width: 100%;
  }

  .produtos-grid {
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  }
}
```

---

## ⚡ Quick Start (5 minutos)

### Teste rápido da API com curl:

```bash
# Listar categorias
curl http://localhost:8000/categorias

# Criar categoria
curl -X POST http://localhost:8000/categorias \
  -H "Content-Type: application/json" \
  -d '{"nome":"Bebidas"}'

# Listar menu
curl http://localhost:8000/menu

# Criar pedido
curl -X POST http://localhost:8000/pedidos \
  -H "Content-Type: application/json" \
  -d '{
    "id_estabelecimento": 1,
    "itens": [
      {"id_menu": 1, "quantidade": 2},
      {"id_menu": 2, "quantidade": 1}
    ]
  }'
```

---

## 📱 Variáveis de Ambiente

Crie arquivo `.env`:
```
REACT_APP_API_URL=http://localhost:8000
REACT_APP_ESTABELECIMENTO_ID=1
```

---

## 🧪 Testes da API (Sem Frontend)

### Com Postman ou Insomnia:
1. Crie uma coleção "PDV API"
2. Defina `{{baseUrl}}` = `http://localhost:8000`
3. Adicione requisições para cada endpoint

---

## 🐛 Troubleshooting

| Problema | Solução |
|----------|---------|
| CORS Error | Certificar que CORS foi habilitado no FastAPI |
| 404 Endpoints | Implementar os endpoints faltantes |
| Timeout | Aumentar timeout em axios config |
| Dados não aparecem | Verificar console do navegador para erros |

---

## ✨ Próximos passos

1. ✅ Testar endpoints com curl/Postman
2. ✅ Instalar dependências do frontend
3. ✅ Criar estrutura de componentes
4. ✅ Implementar hooks customizados
5. ✅ Integrar componentes
6. ✅ Adicionar autenticação
7. ✅ Deploy em produção
