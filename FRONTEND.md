# Próximos Passos — Frontend

Guia para construção do frontend que irá consumir a API do Fórum Flask.

## Stack Sugerida

- **React** (ou Next.js) com TypeScript
- **Tailwind CSS** para estilização
- **Axios** para chamadas HTTP
- **React Router** para navegação
- **Context API** ou **Zustand** para gerenciamento de estado (auth)

## Estrutura Sugerida de Páginas

```
frontend/
├── src/
│   ├── pages/
│   │   ├── Home.tsx            # Lista de posts do fórum
│   │   ├── Login.tsx           # Formulário de login
│   │   ├── Cadastro.tsx        # Formulário de cadastro
│   │   ├── PostDetalhe.tsx     # Post completo + comentários
│   │   ├── NovoPost.tsx        # Formulário para criar post
│   │   └── Usuarios.tsx        # Lista de usuários cadastrados
│   ├── components/
│   │   ├── Header.tsx          # Navbar com login/logout
│   │   ├── PostCard.tsx        # Card de preview do post
│   │   ├── ComentarioItem.tsx  # Componente de comentário
│   │   ├── FormComentario.tsx  # Input para novo comentário
│   │   └── ProtectedRoute.tsx  # Wrapper para rotas autenticadas
│   ├── services/
│   │   └── api.ts              # Configuração do Axios + interceptors
│   ├── contexts/
│   │   └── AuthContext.tsx     # Estado global de autenticação
│   └── types/
│       └── index.ts            # Interfaces TypeScript
```

## Interfaces TypeScript

```typescript
interface Usuario {
  id: number;
  nome: string;
  email: string;
  criado_em: string;
  total_posts: number;
  total_comentarios: number;
}

interface Post {
  id: number;
  titulo: string;
  conteudo: string;
  criado_em: string;
  autor: { id: number; nome: string };
  total_comentarios: number;
  comentarios?: Comentario[];
}

interface Comentario {
  id: number;
  conteudo: string;
  criado_em: string;
  autor: { id: number; nome: string };
}

interface LoginResponse {
  token: string;
  usuario: Usuario;
}

interface ErroResponse {
  erro: string;
}
```

## Configuração do Axios

```typescript
// src/services/api.ts
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://<IP_DO_SERVIDOR>:5000',
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
```

## Mapeamento de Rotas do Frontend → API

| Página Frontend  | Rota Frontend    | Chamada à API                | Método | Auth |
|-----------------|------------------|------------------------------|--------|------|
| Home            | `/`              | `GET /posts`                 | GET    | Não  |
| Login           | `/login`         | `POST /login`                | POST   | Não  |
| Cadastro        | `/cadastro`      | `POST /cadastro`             | POST   | Não  |
| Detalhe do Post | `/posts/:id`     | `GET /posts/:id`             | GET    | Não  |
| Novo Post       | `/novo-post`     | `POST /posts`                | POST   | Sim  |
| Comentar        | `/posts/:id`     | `POST /posts/:id/comentarios`| POST   | Sim  |
| Deletar Post    | `/posts/:id`     | `DELETE /posts/:id`          | DELETE | Sim  |
| Usuários        | `/usuarios`      | `GET /usuarios`              | GET    | Não  |

## Fluxo de Autenticação

1. Usuário preenche o formulário de **cadastro** → `POST /cadastro`
2. Usuário faz **login** → `POST /login` → recebe `token` JWT
3. Salvar o `token` no `localStorage`
4. Enviar o token em toda requisição autenticada via header `Authorization: Bearer <token>`
5. Token expira em **24 horas** — redirecionar para login quando receber `401`

## CORS (importante)

O backend atualmente **não tem CORS habilitado**. Antes de integrar o frontend, adicionar ao backend:

```bash
pip install flask-cors
```

```python
from flask_cors import CORS
CORS(app)
```

Ou, no `requirements.txt`, adicionar `flask-cors`.

## Checklist de Implementação

- [ ] Criar projeto React/Next.js com TypeScript
- [ ] Configurar Tailwind CSS
- [ ] Criar serviço de API (Axios com interceptors)
- [ ] Implementar AuthContext (login, logout, token)
- [ ] Página de Cadastro (formulário + validação)
- [ ] Página de Login (formulário + redirecionamento)
- [ ] Página Home (listagem de posts com PostCard)
- [ ] Página de Detalhe do Post (post + comentários + form de comentário)
- [ ] Página de Novo Post (formulário autenticado)
- [ ] Botão de Deletar Post (visível apenas para o autor)
- [ ] Página de Usuários (listagem)
- [ ] Header/Navbar (navegação + estado logado/deslogado)
- [ ] ProtectedRoute (redirecionar se não autenticado)
- [ ] Habilitar CORS no backend
- [ ] Deploy do frontend (Vercel, Netlify ou servir via Nginx no EC2)
