from flask import Flask, request, redirect, url_for, render_template, session, jsonify
import psycopg2
import os
from flask_mail import Mail, Message
import secrets

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'

# ==============================
# BANCO DE DADOS
# ==============================

DB_HOST = '103.199.186.165'
DB_NAME = 'teste'
DB_USER = 'msconnect'
DB_PASS = 'Ms@2025intelCBA'


def get_db_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        client_encoding='utf8'
    )
    return conn


# ==============================
# HOME
# ==============================

@app.route('/')
def index():
    return render_template('index.html')


# ==============================
# CADASTRO
# ==============================

@app.route('/cadastrar', methods=['POST'])
def cadastrar():
    nome = request.form['nome']
    email = request.form['email']
    senha = request.form['senha']

    if not email.endswith('@msconnect.com.br'):
        return 'Apenas emails corporativos são permitidos.', 400

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO usuarios (nome, email, senha)
        VALUES (%s, %s, %s)
    """, (nome, email, senha))

    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for('index'))


# ==============================
# LOGIN
# ==============================

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    senha = request.form['senha']

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, nome, email
        FROM usuarios
        WHERE email = %s AND senha = %s
    """, (email, senha))

    usuario = cur.fetchone()

    cur.close()
    conn.close()

    if usuario:
        session['usuario_id'] = usuario[0]
        session['nome_usuario'] = usuario[1]
        session['email_usuario'] = usuario[2]

        return redirect(url_for('painel'))
    else:
        return 'Login inválido'


# ==============================
# PAINEL
# ==============================

@app.route('/painel')
def painel():
    if 'email_usuario' not in session:
        return redirect(url_for('index'))

    return render_template(
        'painel.html',
        nome_usuario=session.get('nome_usuario')
    )


# ==============================
# VALIDAÇÃO DE PERMISSÃO
# ==============================

@app.route('/validar-dashboard/<dashboard>')
def validar_dashboard(dashboard):
    if 'email_usuario' not in session:
        return jsonify({
            "permitido": False,
            "mensagem": "Usuário não autenticado."
        })

    email = session.get('email_usuario')

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id
        FROM permissoes_dashboard
        WHERE email = %s
        AND dashboard = %s
    """, (email, dashboard))

    permissao = cur.fetchone()

    cur.close()
    conn.close()

    if permissao:
        return jsonify({
            "permitido": True
        })
    else:
        return jsonify({
            "permitido": False,
            "mensagem": "Você não possui permissão para acessar este dashboard."
        })


# ==============================
# LOGOUT
# ==============================

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


# ==============================
# RESET DE SENHA (mantido)
# ==============================

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'seu_email@gmail.com'
app.config['MAIL_PASSWORD'] = 'sua_senha_do_email'

mail = Mail(app)


@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT * FROM usuarios
            WHERE email = %s
        """, (email,))

        usuario = cur.fetchone()

        cur.close()
        conn.close()

        if usuario:
            token = secrets.token_hex(16)

            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("""
                UPDATE usuarios
                SET reset_token = %s
                WHERE email = %s
            """, (token, email))

            conn.commit()
            cur.close()
            conn.close()

            reset_link = url_for(
                'reset_password',
                token=token,
                _external=True
            )

            msg = Message(
                'Redefinição de Senha',
                sender='seu_email@gmail.com',
                recipients=[email]
            )

            msg.body = f'Clique no link para redefinir sua senha: {reset_link}'
            mail.send(msg)

            return 'Um e-mail foi enviado com instruções para redefinir sua senha.'

        return 'E-mail não encontrado.'

    return render_template('forgot_password.html')


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM usuarios
        WHERE reset_token = %s
    """, (token,))

    usuario = cur.fetchone()

    cur.close()
    conn.close()

    if not usuario:
        return 'Token inválido ou expirado.'

    if request.method == 'POST':
        nova_senha = request.form['nova_senha']

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            UPDATE usuarios
            SET senha = %s,
                reset_token = NULL
            WHERE reset_token = %s
        """, (nova_senha, token))

        conn.commit()
        cur.close()
        conn.close()

        return 'Sua senha foi redefinida com sucesso!'

    return render_template('reset_password.html', token=token)


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)