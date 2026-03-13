# Forum Flask API

API REST de um fórum simples com sistema de cadastro, autenticação JWT e posts com comentários. Backend em Flask com PostgreSQL, rodando em containers Docker na AWS EC2.

## Tecnologias

- **Python 3.9** + **Flask 2.0**
- **PostgreSQL 13** (container Docker)
- **SQLAlchemy** (ORM)
- **PyJWT** (autenticação via token)
- **Docker** + **Docker Compose**

## Estrutura do Projeto

```
projeto-flask-ec2/
├── app.py               # Aplicação principal (rotas, models, auth)
├── requirements.txt     # Dependências Python
├── Dockerfile           # Imagem Docker da aplicação
├── docker-compose.yml   # Orquestração dos containers (web + db)
└── README.md
```

## Como Rodar

### Com Docker (recomendado)

```bash
docker-compose up --build -d
```

A API estará disponível em `http://localhost:5000`.

### Sem Docker (desenvolvimento local)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 app.py
```

> Localmente sem Docker, é preciso ter um PostgreSQL rodando e configurar as variáveis de ambiente (ver abaixo).

## Variáveis de Ambiente

| Variável     | Padrão                        | Descrição               |
|--------------|-------------------------------|-------------------------|
| `DB_USER`    | `admin`                       | Usuário do PostgreSQL   |
| `DB_PASS`    | `password`                    | Senha do PostgreSQL     |
| `DB_HOST`    | `db`                          | Host do banco           |
| `DB_PORT`    | `5432`                        | Porta do banco          |
| `DB_NAME`    | `meubanco`                    | Nome do banco           |
| `SECRET_KEY` | `chave-secreta-dev-2026`      | Chave para assinar JWT  |

## Rotas da API

### Públicas

| Método | Rota              | Descrição                    | Body (JSON)                                  |
|--------|--------------------|------------------------------|----------------------------------------------|
| GET    | `/`               | Info da API e rotas          | -                                            |
| POST   | `/cadastro`       | Cadastrar usuário            | `{"nome", "email", "senha"}`                 |
| POST   | `/login`          | Login (retorna JWT)          | `{"email", "senha"}`                         |
| GET    | `/usuarios`       | Listar todos os usuários     | -                                            |
| GET    | `/posts`          | Listar posts do fórum        | -                                            |
| GET    | `/posts/<id>`     | Ver post com comentários     | -                                            |

### Autenticadas (enviar header `Authorization: Bearer <token>`)

| Método | Rota                        | Descrição                  | Body (JSON)                    |
|--------|-----------------------------|----------------------------|--------------------------------|
| POST   | `/posts`                    | Criar novo post            | `{"titulo", "conteudo"}`       |
| DELETE | `/posts/<id>`               | Deletar post (só o autor)  | -                              |
| POST   | `/posts/<id>/comentarios`   | Comentar em um post        | `{"conteudo"}`                 |

## Exemplos de Uso (curl)

### Cadastrar usuário

```bash
curl -X POST http://localhost:5000/cadastro \
  -H "Content-Type: application/json" \
  -d '{"nome":"João","email":"joao@email.com","senha":"123456"}'
```

### Login

```bash
curl -X POST http://localhost:5000/login \
  -H "Content-Type: application/json" \
  -d '{"email":"joao@email.com","senha":"123456"}'
```

### Criar post (autenticado)

```bash
curl -X POST http://localhost:5000/posts \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer SEU_TOKEN_AQUI" \
  -d '{"titulo":"Meu primeiro post","conteudo":"Conteúdo do post"}'
```

### Comentar em um post

```bash
curl -X POST http://localhost:5000/posts/1/comentarios \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer SEU_TOKEN_AQUI" \
  -d '{"conteudo":"Ótimo post!"}'
```

## Banco de Dados

### Tabelas

- **usuarios** — id, nome, email, senha_hash, criado_em
- **posts** — id, titulo, conteudo, criado_em, autor_id (FK → usuarios)
- **comentarios** — id, conteudo, criado_em, autor_id (FK → usuarios), post_id (FK → posts)

Os dados são persistidos em um volume Docker (`pgdata`), garantindo que sobrevivem a restarts dos containers.

## Deploy na AWS EC2

A aplicação roda em uma instância EC2 com Docker e Docker Compose instalados.

```bash
# Enviar arquivos
scp -i chave-servidor.pem app.py requirements.txt docker-compose.yml Dockerfile ubuntu@<IP_EC2>:~/projeto-flask-ec2/

# Conectar via SSH
ssh -i chave-servidor.pem ubuntu@<IP_EC2>

# No servidor, rebuild e restart
cd ~/projeto-flask-ec2
sudo docker-compose down
sudo docker-compose up --build -d
sudo docker-compose logs -f
```
