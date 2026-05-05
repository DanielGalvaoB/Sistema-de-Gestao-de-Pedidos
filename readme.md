# 📚 API de Categorias, Estabelecimentos e Menu

* Categorias
* Estabelecimentos
* Menu

---

## 🚀 Tecnologias utilizadas

* FastAPI
* SQLAlchemy
* Pydantic
* Python 3.x

---

## 📂 Estrutura do Projeto

```
app/
├── crud/
├── dependencies/
├── models/
├── routers/
├── schemas/
```

---

# 🏷️ Categorias (`/categorias`)

## ➕ Criar categoria

**POST** `/categorias/`

### Body:

```json
{
  "nome": "string"
}
```

### Response:

```json
{
  "id": 1,
  "nome": "string"
}
```

---

## 📄 Listar categorias

**GET** `/categorias/`

---

## 🔍 Buscar categoria

**GET** `/categorias/{categoria_id}`

---

## ✏️ Atualizar (PUT)

**PUT** `/categorias/{categoria_id}`

---

## 🩹 Atualizar (PATCH)

**PATCH** `/categorias/{categoria_id}`

---

## ❌ Deletar

**DELETE** `/categorias/{categoria_id}`

---

# 🏢 Estabelecimentos (`/estabelecimentos`)

## ➕ Criar

**POST** `/estabelecimentos/`

### Body:

```json
{
  "nome": "string",
  "email": "string"
}
```

### Erros:

* 400: Email já cadastrado

---

## 📄 Listar

**GET** `/estabelecimentos/`

---

## 🔍 Buscar

**GET** `/estabelecimentos/{id}`

### Erros:

* 404: Não encontrado

---

## 🩹 Atualizar

**PATCH** `/estabelecimentos/{id}`

---

## ❌ Deletar

**DELETE** `/estabelecimentos/{id}`

---

# 🍽️ Menu (`/menu`)

## ➕ Criar

**POST** `/menu/`

---

## 📄 Listar

**GET** `/menu/`

> Retorna `null` se não houver registros

---

## 🔍 Buscar

**GET** `/menu/{menu_id}`

### Erros:

* 404: Menu não encontrado

---

## 🩹 Atualizar

**PATCH** `/menu/{menu_id}`

---

## ❌ Deletar

**DELETE** `/menu/{menu_id}`

---

# ⚠️ Códigos de Status

| Código | Descrição            |
| ------- | ---------------------- |
| 200     | OK                     |
| 201     | Criado                 |
| 204     | Sem conteúdo          |
| 400     | Requisição inválida |
| 404     | Não encontrado        |

---

# 🔌 Banco de Dados

As rotas utilizam a dependência:

```python
db: Session = Depends(get_db)
```

Responsável por fornecer a sessão do banco.

---

# 📌 Observações

* Algumas rotas não tratam retorno `None`
* O endpoint de menu pode retornar `null`
* Falta padronização em mensagens de erro

---

# ✅ Melhorias Futuras

* Padronizar erros
* Adicionar autenticação
* Implementar paginação
* Melhorar validações
* Criar testes automatizados

---
