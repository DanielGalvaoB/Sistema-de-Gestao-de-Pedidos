# Sistema de Gestão de Pedidos (PDV)

Sistema para restaurantes e lanchonetes com:

- Cardápio digital por QR Code (mesa ou balcão).
- Painel da cozinha (KDS) em tempo real.
- Contas por mesa com pagamentos parciais.
- Cobrança PIX (BR Code).
- Controle financeiro e relatórios.

| Camada   | Tecnologias |
| -------- | ----------- |
| Backend  | Python 3.12, FastAPI, SQLAlchemy 2, Pydantic v2, Alembic, SQLite, Pytest |
| Frontend | React 18, TypeScript, Vite, React Router, Recharts, qrcode.react |

```
app/                 Backend (FastAPI)
├── core/            config, segurança (bcrypt/JWT), erros, PIX, tempo real
├── crud/            regras de negócio e acesso a dados
├── dependencies/    sessão do banco e autenticação/permissões
├── models/          modelos SQLAlchemy
├── routers/         rotas da API
└── schemas/         schemas Pydantic
alembic/             migrações (única forma de criar/atualizar o banco)
frontend/            React + TypeScript (Vite)
scripts/seed_demo.py dados de demonstração
tests/               testes automatizados (pytest)
```

---

## Como executar (Windows)

Pré-requisitos: Python 3.12+ e Node.js 20+.

### Backend

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env          # edite SECRET_KEY
alembic upgrade head            # cria/atualiza o banco
python -m scripts.seed_demo     # opcional: dados de demonstração
fastapi dev app/app.py          # http://127.0.0.1:8000  (docs em /docs)
```

### Frontend

```bash
cd frontend
npm install
npm run dev                     # http://localhost:5173
```

O Vite encaminha `/api/*` (inclusive WebSocket) para `http://127.0.0.1:8000`.

### Acesso pelo celular

1. Rode `npm run dev` (ele já usa `--host`).
2. No `.env` do backend, defina `FRONTEND_URL=http://<IP-do-PC>:5173`. Esse endereço vai nos QR Codes.
3. Imprima os QR Codes em **Mesas → QR Code**.

### Usuários de demonstração (`scripts/seed_demo.py`)

Senha `demo12345` para todos:

| Email                  | Perfil        |
| ---------------------- | ------------- |
| admin@example.com      | Administrador |
| atendente@example.com  | Atendente     |
| cozinha@example.com    | Cozinha       |
| financeiro@example.com | Financeiro    |

Cardápio público da demo: `http://localhost:5173/c/lanchonete-demo`.

### Testes e qualidade

```bash
pytest -q          # 56 testes (API, regras de negócio, migrações, WebSocket)
ruff check .
cd frontend && npm run build   # type-check + build de produção
```

---

## Variáveis de ambiente (`.env`)

| Variável                      | Padrão                         | Descrição |
| ----------------------------- | ------------------------------ | --------- |
| `DATABASE_URL`                | `sqlite:///./peccai.db`        | URL do banco |
| `SECRET_KEY`                  | (troque!)                      | Chave de assinatura dos tokens JWT |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `720`                          | Validade do login |
| `BCRYPT_ROUNDS`               | `12`                           | Custo do hash de senha |
| `CORS_ORIGINS`                | `http://localhost:5173,...`    | Origens permitidas, separadas por vírgula |
| `FRONTEND_URL`                | `http://localhost:5173`        | Base dos links dos QR Codes |
| `APP_TIMEZONE`                | `America/Sao_Paulo`            | Fuso usado nos relatórios por dia |

Frontend (`frontend/.env`):

- `VITE_API_URL`: padrão `/api`.
- `API_PROXY_TARGET`: padrão `http://127.0.0.1:8000`.

---

## Perfis e permissões

| Perfil        | Acesso |
| ------------- | ------ |
| Administrador | Tudo, incluindo usuários, configurações, produtos e mesas |
| Atendente     | Pedidos, mesas, contas e pagamentos. Pode lançar acréscimos, mas **não** dá desconto |
| Cozinha       | Painel da cozinha: ver pedidos e alterar status e previsão |
| Financeiro    | Movimentações, relatórios, contas, pagamentos e descontos |

As rotas `/public/*` não exigem login: cardápio, envio de pedido e acompanhamento. Senhas são guardadas com bcrypt e nunca aparecem nas respostas da API.

---

## Endpoints principais

Documentação interativa completa em `http://127.0.0.1:8000/docs`. O botão **Authorize** usa `/auth/token`.

### Autenticação e usuários

| Método | Rota | Descrição |
| --- | --- | --- |
| POST | `/estabelecimentos/` | Cadastro público: cria a loja e o usuário admin |
| POST | `/auth/login` | `{email, password}` → `{access_token}` |
| POST | `/auth/token` | Mesmo login, no formato OAuth2 (form) |
| GET | `/auth/me` | Usuário logado |
| GET/POST | `/usuarios/` | Listar/criar usuários (admin) |
| PATCH | `/usuarios/{id}` | Editar perfil, ativo ou senha (a senha é gravada com hash) |
| PATCH | `/usuarios/me/senha` | Trocar a própria senha |
| GET | `/estabelecimentos/me` | Dados e configurações da loja |
| PATCH | `/estabelecimentos/{id}` | Atualizar a loja (email duplicado → 409) |
| GET | `/estabelecimentos/me/qrcode` | URL do cardápio geral |

### Cardápio

| Método | Rota | Descrição |
| --- | --- | --- |
| GET/POST | `/categorias/` | Listar/criar |
| GET | `/categorias/{id}` | Buscar (404 se não existir) |
| PUT | `/categorias/{id}` | Substituição completa (`nome` obrigatório) |
| PATCH | `/categorias/{id}` | Atualização parcial |
| DELETE | `/categorias/{id}` | 409 se houver produtos vinculados |
| GET | `/menu/?busca=&id_categoria=&disponivel=` | Lista sempre um array (vazio se não houver produtos) |
| POST | `/menu/` | Criar produto |
| PATCH | `/menu/{id}` | Editar. Mudança de preço vai para o histórico |
| GET | `/menu/{id}/historico-precos` | Histórico de preços |
| DELETE | `/menu/{id}` | Exclui o produto; se já foi vendido, apenas desativa |

### Mesas, pedidos e cozinha

| Método | Rota | Descrição |
| --- | --- | --- |
| GET | `/mesas/` | Mesas com situação (livre/ocupada/aguardando_pagamento) e total |
| POST/PATCH | `/mesas/`, `/mesas/{id}` | Cadastrar, editar ou desativar |
| GET | `/mesas/{id}/qrcode` | URL do cardápio da mesa |
| POST | `/mesas/{id}/regenerar-token` | Invalida o QR Code impresso |
| GET | `/mesas/{id}/historico` | Contas anteriores da mesa |
| POST | `/pedidos/` | Pedido da equipe (`id_mesa`, `id_sessao` ou `tipo` balcão/retirada) |
| GET | `/pedidos/?ativos=true` | Pedidos do painel da cozinha |
| GET | `/pedidos/{id}` | Detalhe com histórico de status |
| PATCH | `/pedidos/{id}/status` | Status do pedido inteiro |
| PATCH | `/pedidos/{id}/itens/{item}/status` | Status de um item |
| PATCH | `/pedidos/{id}/previsao` | `{minutos_adicionais, motivo_atraso}` |
| WS | `/ws/pedidos?token=` | Avisa os clientes quando há mudanças |

Exemplo de pedido:

```json
POST /pedidos/
{ "id_mesa": 3, "itens": [{ "id_menu": 1, "quantidade": 2, "observacao": "sem cebola" }] }
```

O preço **sempre** vem do banco. Valores enviados pelo cliente são ignorados.

### Contas e pagamentos

| Método | Rota | Descrição |
| --- | --- | --- |
| GET/POST | `/contas/` | Listar contas (`?status=aberta`) ou abrir uma conta |
| GET | `/contas/{id}` | Pedidos, pagamentos e resumo (subtotal, desconto, acréscimo, total, pago, saldo) |
| PATCH | `/contas/{id}/ajustes` | Desconto (com motivo), acréscimo ou taxa de serviço |
| POST | `/contas/{id}/solicitar-fechamento` | Mesa passa a "aguardando pagamento" |
| POST | `/contas/{id}/pagamentos` | Registro **manual** de pagamento (`chave_idempotencia` obrigatória) |
| POST | `/contas/pagamentos/{id}/estornar` | Estorno com motivo (a receita é cancelada, não apagada) |
| POST | `/contas/{id}/encerrar` | Recusado se houver saldo ou pedidos não entregues |
| POST/GET | `/contas/{id}/pix` | Gerar/listar cobranças PIX |

Exemplo de pagamento:

```json
POST /contas/1/pagamentos
{ "valor": "30.00", "metodo": "dinheiro", "chave_idempotencia": "b6c1e0f2-..." }
```

### Financeiro e relatórios

| Método | Rota | Descrição |
| --- | --- | --- |
| GET/POST/PATCH | `/financeiro/categorias` | Categorias financeiras |
| GET/POST | `/financeiro/movimentacoes` | Listar (filtros: período, tipo, categoria, método, status) e lançar |
| PATCH | `/financeiro/movimentacoes/{id}` | Editar lançamento manual |
| POST | `/financeiro/movimentacoes/{id}/cancelar` | Cancelar com motivo (fica no histórico) |
| GET | `/relatorios/resumo?inicio=&fim=` | Indicadores, série diária e rankings |
| GET | `/relatorios/extrato.csv` / `.pdf` | Exportação do extrato |

### Público (sem login)

| Método | Rota | Descrição |
| --- | --- | --- |
| GET | `/public/{slug}?mesa={token}` | Cardápio (categorias e produtos ativos) |
| POST | `/public/{slug}/pedidos` | Envia o pedido e devolve `codigo_acompanhamento` |
| GET | `/public/pedidos/{codigo}` | Acompanhamento sem dados pessoais |

---

## Regras de negócio importantes

- **Preço congelado.** Cada item do pedido guarda o nome e o preço do momento da compra. Alterar o produto não muda pedidos antigos.
- **Transações.** Um pedido e seus itens são gravados juntos. Se um item for inválido, nada é gravado.
- **Status por item.** O pedido só fica "pronto" quando todos os itens ativos estão prontos. Existe uma exceção explícita: o botão "Tudo pronto" da cozinha marca todos os itens ativos.
- **Atraso.** O prazo previsto é o maior tempo de preparo entre os itens do pedido (ou o padrão da loja).
  - O alerta aparece a partir do percentual configurado.
  - O atraso de cada item é calculado separadamente.
  - Ao atualizar a previsão, o motivo informado aparece para o cliente.
- **Contas.** Uma mesa tem no máximo uma conta aberta (garantido por índice único parcial). Balcão e retirada geram uma conta por cliente.
- **Pagamentos.**
  - Nunca ultrapassam o saldo.
  - A `chave_idempotencia` evita duplicidade em cliques repetidos.
  - Cada pagamento gera **uma** entrada na categoria "Vendas" (restrição `UNIQUE`).
  - Pedido criado não conta como dinheiro recebido.
- **Histórico auditável.** Movimentações e pagamentos não são excluídos; usam cancelamento ou estorno com motivo, data e usuário. Produtos já vendidos são desativados em vez de apagados.
- **Integridade.** Foreign keys do SQLite estão ativas (`PRAGMA foreign_keys=ON`), com `RESTRICT` nas relações históricas.
- **Critérios dos relatórios** (as métricas não se misturam):
  - **Vendas:** pela data do pedido, valor bruto dos itens.
  - **Recebido:** pela data do pagamento.
  - **Despesas:** pela data da movimentação.
  - **A receber:** saldo das contas abertas no período.

---

## Limitações conhecidas / próximos passos

- **PIX.** O sistema gera um BR Code **estático** válido (copia e cola + QR Code) a partir da chave PIX da loja. Mas **não há provedor integrado**, então o recebimento **não é confirmado automaticamente**: o funcionário confere no banco e registra o pagamento manualmente. A estrutura (`CobrancaPix.provedor`, `origem='provedor'` no pagamento) está pronta para um provedor com webhook autenticado.
- **Tempo real.** O WebSocket usa sinalização em memória e funciona com **um processo** do servidor. Para vários workers, troque `app/core/realtime.py` por Redis pub/sub. Se o WebSocket cair, o frontend usa atualização periódica.
- **Pedidos públicos** não têm limite de requisições (rate limiting). Recomenda-se um proxy (nginx/Cloudflare) em produção.
- **Notificações externas** (WhatsApp/SMS/push) não foram implementadas. O cliente acompanha pela página do pedido.
- **SQLite** atende uma loja. Para mais carga, use PostgreSQL alterando `DATABASE_URL` (as migrações já usam `render_as_batch`).
- **Migrações.** O histórico foi reiniciado em `78a468eea797_schema_inicial_completo`, porque a migração antiga só adicionava uma coluna e não criava o banco. Um banco antigo criado com `create_all` não é compatível: crie um novo com `alembic upgrade head`.
