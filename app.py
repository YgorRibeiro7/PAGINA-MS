from flask import Flask, request, redirect, url_for, render_template, session
import psycopg2
import os
from flask_mail import Mail, Message
import secrets

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'

# Configurações do banco de dados
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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/cadastrar', methods=['POST'])
def cadastrar():
    nome = request.form['nome']
    email = request.form['email']
    senha = request.form['senha']
    
     # Validação do email corporativo
    if not email.endswith('@msconnect.com.br'):
        return 'Apenas emails corporativos são permitidos.', 400
    
    print(f"Dados recebidos: nome={nome}, email={email}, senha={senha}")  # Log dos dados

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        'INSERT INTO usuarios (nome, email, senha) VALUES (%s, %s, %s)',
        (nome, email, senha)
    )
    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for('index'))

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    senha = request.form['senha']

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        'SELECT * FROM usuarios WHERE email = %s AND senha = %s',
        (email, senha)
    )
    usuario = cur.fetchone()
    cur.close()
    conn.close()

    if usuario:
        nome_usuario = usuario[1]  # Use o valor diretamente
        session['usuario'] = nome_usuario
        return redirect(url_for('pagina2'))
    else:
      return 'Login falhou. Verifique suas credenciais.'

@app.route('/pagina2')
def pagina2():
    if 'usuario' in session:
        return render_template('pagina2.html')
    else:
        return redirect(url_for('index'))

@app.route('/logout')
def logout():
    # Remove o usuário da sessão
    session.pop('usuario', None)
    # Redireciona para a página inicial
    return redirect(url_for('index'))

# *********** CODIGOS PARA REDEFINIR SENHA

# Configurações do Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Servidor SMTP do Gmail
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'seu_email@gmail.com'  # Seu e-mail
app.config['MAIL_PASSWORD'] = 'sua_senha_do_email'  # Sua senha do e-mail


mail = Mail(app)

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        
        # Verifique se o e-mail existe no banco de dados
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM usuarios WHERE email = %s', (email,))
        usuario = cur.fetchone()
        cur.close()
        conn.close()

        if usuario:
            # Gere um token único
            token = secrets.token_hex(16)
            
            # Salve o token no banco de dados
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('UPDATE usuarios SET reset_token = %s WHERE email = %s', (token, email))
            conn.commit()
            cur.close()
            conn.close()

            # Envie o e-mail com o link de redefinição
            reset_link = url_for('reset_password', token=token, _external=True)
            msg = Message('Redefinição de Senha', sender='seu_email@gmail.com', recipients=[email])
            msg.body = f'Clique no link para redefinir sua senha: {reset_link}'
            mail.send(msg)

            return 'Um e-mail foi enviado com instruções para redefinir sua senha.'
        else:
            return 'E-mail não encontrado.'

    return render_template('forgot_password.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    # Verifique se o token é válido
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM usuarios WHERE reset_token = %s', (token,))
    usuario = cur.fetchone()
    cur.close()
    conn.close()

    if not usuario:
        return 'Token inválido ou expirado.'

    if request.method == 'POST':
        nova_senha = request.form['nova_senha']
        
        # Atualize a senha no banco de dados
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('UPDATE usuarios SET senha = %s, reset_token = NULL WHERE reset_token = %s', (nova_senha, token))
        conn.commit()
        cur.close()
        conn.close()

        return 'Sua senha foi redefinida com sucesso!'

    return render_template('reset_password.html', token=token)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Usa a porta do Render ou 5000 como fallback
    app.run(host='0.0.0.0', port=port)
    # app.run(debug=True)