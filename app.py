from flask import Flask, request, redirect, url_for, render_template, session
import psycopg2

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
if __name__ == '__main__':
    app.run(debug=True)