from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from functools import wraps
import jwt
import os
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'chave-secreta-dev-2026')

DB_USER = os.environ.get('DB_USER', 'admin')
DB_PASS = os.environ.get('DB_PASS', 'password')
DB_HOST = os.environ.get('DB_HOST', 'db')
DB_PORT = os.environ.get('DB_PORT', '5432')
DB_NAME = os.environ.get('DB_NAME', 'meubanco')

app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# ===================== MODELS =====================

class User(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(256), nullable=False)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    posts = db.relationship('Post', backref='autor', lazy=True)
    comentarios = db.relationship('Comentario', backref='autor', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'email': self.email,
            'criado_em': self.criado_em.isoformat(),
            'total_posts': len(self.posts),
            'total_comentarios': len(self.comentarios),
        }


class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    conteudo = db.Column(db.Text, nullable=False)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    autor_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    comentarios = db.relationship('Comentario', backref='post', lazy=True, cascade='all, delete-orphan')

    def to_dict(self, incluir_comentarios=False):
        data = {
            'id': self.id,
            'titulo': self.titulo,
            'conteudo': self.conteudo,
            'criado_em': self.criado_em.isoformat(),
            'autor': {'id': self.autor.id, 'nome': self.autor.nome},
            'total_comentarios': len(self.comentarios),
        }
        if incluir_comentarios:
            data['comentarios'] = [c.to_dict() for c in self.comentarios]
        return data


class Comentario(db.Model):
    __tablename__ = 'comentarios'
    id = db.Column(db.Integer, primary_key=True)
    conteudo = db.Column(db.Text, nullable=False)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    autor_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'conteudo': self.conteudo,
            'criado_em': self.criado_em.isoformat(),
            'autor': {'id': self.autor.id, 'nome': self.autor.nome},
        }


# ===================== AUTH - API (JWT) =====================

def token_obrigatorio(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'erro': 'Token não fornecido'}), 401
        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            usuario_atual = User.query.get(payload['user_id'])
            if not usuario_atual:
                return jsonify({'erro': 'Usuário não encontrado'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'erro': 'Token expirado'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'erro': 'Token inválido'}), 401
        return f(usuario_atual, *args, **kwargs)
    return decorated


# ===================== AUTH - WEB (Session) =====================

def login_obrigatorio(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('user_id'):
            flash('Faça login para acessar esta página.', 'error')
            return redirect(url_for('pagina_login'))
        return f(*args, **kwargs)
    return decorated


# ===================== ROTAS WEB (HTML) =====================

@app.route('/')
def pagina_home():
    posts = Post.query.order_by(Post.criado_em.desc()).all()
    return render_template('home.html', posts=posts)


@app.route('/web/login', methods=['GET', 'POST'])
def pagina_login():
    if session.get('user_id'):
        return redirect(url_for('pagina_home'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        senha = request.form.get('senha', '')

        usuario = User.query.filter_by(email=email).first()
        if usuario and check_password_hash(usuario.senha_hash, senha):
            session['user_id'] = usuario.id
            session['user_nome'] = usuario.nome
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('pagina_home'))

        flash('Email ou senha incorretos.', 'error')

    return render_template('login.html')


@app.route('/web/cadastro', methods=['GET', 'POST'])
def pagina_cadastro():
    if session.get('user_id'):
        return redirect(url_for('pagina_home'))

    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip()
        senha = request.form.get('senha', '')

        if not nome or not email or not senha:
            flash('Todos os campos são obrigatórios.', 'error')
            return render_template('cadastro.html')

        if len(senha) < 6:
            flash('A senha deve ter pelo menos 6 caracteres.', 'error')
            return render_template('cadastro.html')

        if User.query.filter_by(email=email).first():
            flash('Este email já está cadastrado.', 'error')
            return render_template('cadastro.html')

        usuario = User(
            nome=nome,
            email=email,
            senha_hash=generate_password_hash(senha),
        )
        db.session.add(usuario)
        db.session.commit()

        session['user_id'] = usuario.id
        session['user_nome'] = usuario.nome
        flash('Conta criada com sucesso!', 'success')
        return redirect(url_for('pagina_home'))

    return render_template('cadastro.html')


@app.route('/web/logout')
def pagina_logout():
    session.clear()
    flash('Você saiu da sua conta.', 'success')
    return redirect(url_for('pagina_home'))


@app.route('/web/posts/novo', methods=['GET', 'POST'])
@login_obrigatorio
def pagina_novo_post():
    if request.method == 'POST':
        titulo = request.form.get('titulo', '').strip()
        conteudo = request.form.get('conteudo', '').strip()

        if not titulo or not conteudo:
            flash('Título e conteúdo são obrigatórios.', 'error')
            return render_template('novo_post.html')

        post = Post(titulo=titulo, conteudo=conteudo, autor_id=session['user_id'])
        db.session.add(post)
        db.session.commit()

        flash('Post publicado com sucesso!', 'success')
        return redirect(url_for('pagina_post', post_id=post.id))

    return render_template('novo_post.html')


@app.route('/web/posts/<int:post_id>')
def pagina_post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post_detalhe.html', post=post)


@app.route('/web/posts/<int:post_id>/comentar', methods=['POST'])
@login_obrigatorio
def pagina_comentar(post_id):
    post = Post.query.get_or_404(post_id)
    conteudo = request.form.get('conteudo', '').strip()

    if not conteudo:
        flash('O comentário não pode estar vazio.', 'error')
        return redirect(url_for('pagina_post', post_id=post.id))

    comentario = Comentario(conteudo=conteudo, autor_id=session['user_id'], post_id=post.id)
    db.session.add(comentario)
    db.session.commit()

    flash('Comentário adicionado!', 'success')
    return redirect(url_for('pagina_post', post_id=post.id))


@app.route('/web/posts/<int:post_id>/deletar', methods=['POST'])
@login_obrigatorio
def pagina_deletar_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.autor_id != session['user_id']:
        flash('Você só pode deletar seus próprios posts.', 'error')
        return redirect(url_for('pagina_post', post_id=post.id))

    db.session.delete(post)
    db.session.commit()
    flash('Post deletado com sucesso.', 'success')
    return redirect(url_for('pagina_home'))


@app.route('/web/usuarios')
def pagina_usuarios():
    usuarios = User.query.order_by(User.criado_em.desc()).all()
    return render_template('usuarios.html', usuarios=usuarios)


# ===================== ROTAS API (JSON) =====================

@app.route('/api')
def api_home():
    return jsonify({
        'mensagem': 'API do Fórum Flask + PostgreSQL',
        'rotas': {
            'POST /api/cadastro': 'Cadastrar novo usuário',
            'POST /api/login': 'Login (retorna JWT)',
            'GET /api/usuarios': 'Listar usuários',
            'GET /api/posts': 'Listar posts do fórum',
            'POST /api/posts': 'Criar post (auth)',
            'GET /api/posts/<id>': 'Ver post com comentários',
            'DELETE /api/posts/<id>': 'Deletar post (auth)',
            'POST /api/posts/<id>/comentarios': 'Comentar em post (auth)',
        }
    })


@app.route('/api/cadastro', methods=['POST'])
def api_cadastro():
    dados = request.get_json()
    if not dados:
        return jsonify({'erro': 'Corpo da requisição vazio'}), 400

    campos = ['nome', 'email', 'senha']
    for campo in campos:
        if not dados.get(campo):
            return jsonify({'erro': f'Campo "{campo}" é obrigatório'}), 400

    if User.query.filter_by(email=dados['email']).first():
        return jsonify({'erro': 'Email já cadastrado'}), 409

    usuario = User(
        nome=dados['nome'],
        email=dados['email'],
        senha_hash=generate_password_hash(dados['senha']),
    )
    db.session.add(usuario)
    db.session.commit()

    return jsonify({'mensagem': 'Usuário cadastrado com sucesso', 'usuario': usuario.to_dict()}), 201


@app.route('/api/login', methods=['POST'])
def api_login():
    dados = request.get_json()
    if not dados or not dados.get('email') or not dados.get('senha'):
        return jsonify({'erro': 'Email e senha são obrigatórios'}), 400

    usuario = User.query.filter_by(email=dados['email']).first()
    if not usuario or not check_password_hash(usuario.senha_hash, dados['senha']):
        return jsonify({'erro': 'Email ou senha incorretos'}), 401

    token = jwt.encode(
        {'user_id': usuario.id, 'exp': datetime.utcnow() + timedelta(hours=24)},
        app.config['SECRET_KEY'],
        algorithm='HS256',
    )

    return jsonify({'token': token, 'usuario': usuario.to_dict()})


@app.route('/api/usuarios', methods=['GET'])
def api_listar_usuarios():
    usuarios = User.query.order_by(User.criado_em.desc()).all()
    return jsonify({'usuarios': [u.to_dict() for u in usuarios], 'total': len(usuarios)})


@app.route('/api/posts', methods=['GET'])
def api_listar_posts():
    posts = Post.query.order_by(Post.criado_em.desc()).all()
    return jsonify({'posts': [p.to_dict() for p in posts], 'total': len(posts)})


@app.route('/api/posts/<int:post_id>', methods=['GET'])
def api_ver_post(post_id):
    post = Post.query.get_or_404(post_id)
    return jsonify({'post': post.to_dict(incluir_comentarios=True)})


@app.route('/api/posts', methods=['POST'])
@token_obrigatorio
def api_criar_post(usuario_atual):
    dados = request.get_json()
    if not dados:
        return jsonify({'erro': 'Corpo da requisição vazio'}), 400

    if not dados.get('titulo') or not dados.get('conteudo'):
        return jsonify({'erro': 'Título e conteúdo são obrigatórios'}), 400

    post = Post(titulo=dados['titulo'], conteudo=dados['conteudo'], autor_id=usuario_atual.id)
    db.session.add(post)
    db.session.commit()

    return jsonify({'mensagem': 'Post criado com sucesso', 'post': post.to_dict()}), 201


@app.route('/api/posts/<int:post_id>', methods=['DELETE'])
@token_obrigatorio
def api_deletar_post(usuario_atual, post_id):
    post = Post.query.get_or_404(post_id)
    if post.autor_id != usuario_atual.id:
        return jsonify({'erro': 'Você só pode deletar seus próprios posts'}), 403

    db.session.delete(post)
    db.session.commit()
    return jsonify({'mensagem': 'Post deletado com sucesso'})


@app.route('/api/posts/<int:post_id>/comentarios', methods=['POST'])
@token_obrigatorio
def api_criar_comentario(usuario_atual, post_id):
    post = Post.query.get_or_404(post_id)
    dados = request.get_json()
    if not dados or not dados.get('conteudo'):
        return jsonify({'erro': 'Conteúdo do comentário é obrigatório'}), 400

    comentario = Comentario(conteudo=dados['conteudo'], autor_id=usuario_atual.id, post_id=post.id)
    db.session.add(comentario)
    db.session.commit()

    return jsonify({'mensagem': 'Comentário adicionado', 'comentario': comentario.to_dict()}), 201


# ===================== INICIALIZAÇÃO =====================

def wait_for_db(retries=10, delay=2):
    for i in range(retries):
        try:
            db.engine.connect()
            print("Banco de dados conectado!")
            return True
        except Exception:
            print(f"Aguardando banco de dados... tentativa {i+1}/{retries}")
            time.sleep(delay)
    raise Exception("Não foi possível conectar ao banco de dados")


if __name__ == '__main__':
    with app.app_context():
        wait_for_db()
        db.create_all()
    app.run(host='0.0.0.0', port=5000)
