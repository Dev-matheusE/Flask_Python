from flask import Flask, render_template, request, redirect, url_for, flash, get_flashed_messages
from flask_sqlalchemy import SQLAlchemy
import pymysql
from werkzeug.security import generate_password_hash, check_password_hash 

pymysql.install_as_MySQLdb()

# --- Configuração da Aplicação ---
app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui_mude_isso' 

# --- Configuração do banco de dados MySQL ---
DB_USER = 'root'
DB_PASSWORD = '1234567'
DB_HOST = '127.0.0.1'
DB_PORT = '3306'
DB_NAME = 'flask_crud_db'

app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- Modelo do Banco de Dados ---
class User(db.Model):
    __tablename__ = 'usuario' # Descomente ou ajuste se o nome da tabela não for 'user'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f"User('{self.id}', '{self.nome}', '{self.email}')"

# --- Rotas ---

@app.route('/')
def index():
    """Rota principal que exibe o formulário de cadastro e a tabela de usuários."""
    users = []
    try:
        users = User.query.all()
    except Exception as e:
        print(f"Erro ao carregar usuários: {e}")
        flash(f"Erro ao carregar usuários: {e}", 'danger')

    # Renderiza o template que contém a lista E o formulário de cadastro
    return render_template('list_and_create.html', users=users, messages=get_flashed_messages(with_categories=True)) # <-- Mudança aqui

# Rota /register permanece a mesma, processa o POST do formulário de cadastro no template 1
@app.route('/register', methods=['POST'])
def register():
    """Rota para processar o cadastro de um novo usuário."""
    # Removida a verificação redundante request.method == 'POST'
    name_form = request.form.get('nome')     # Pega o valor do campo 'nome' do formulário
    email_form = request.form.get('email')   # Pega o valor do campo 'email' do formulário
    password_form = request.form.get('senha')# Pega o valor do campo 'senha' do formulário

    # Usar as variáveis pegas do formulário na validação
    if not name_form or not email_form or not password_form:
        flash('Nome, Email e Senha são obrigatórios.', 'warning')
        print("Tentativa de cadastro com campos vazios.")
        return redirect(url_for('index'))

    # Usar o valor do email do formulário para verificar usuário existente
    existing_user = User.query.filter_by(email=email_form).first()
    if existing_user:
        flash(f'O email {email_form} já está cadastrado.', 'warning')
        print(f"Tentativa de cadastro com email duplicado: {email_form}")
        return redirect(url_for('index'))

    # Usar o valor da senha do formulário para hash
    hashed_password = generate_password_hash(password_form)

    # Criar o novo usuário, passando os valores corretos para as colunas do modelo
    # nome=name_form (passa o valor do campo 'nome' do formulário para a coluna 'nome' do modelo)
    # email=email_form (passa o valor do campo 'email' do formulário para a coluna 'email' do modelo)
    # senha=hashed_password (passa o hash da senha do formulário para a coluna 'senha' do modelo)
    new_user = User(nome=name_form, email=email_form, senha=hashed_password) # <-- CORRETO AGORA

    try:
        db.session.add(new_user)
        db.session.commit()
        flash('Usuário cadastrado com sucesso!', 'success')
        # No log, usar o valor pego do formulário
        print(f"Usuário cadastrado: Nome={name_form}, Email={email_form}")

    except Exception as e:
        db.session.rollback()
        print(f"Erro ao cadastrar usuário: {e}")
        flash(f"Erro ao cadastrar usuário: {e}", 'danger')

    # Redireciona sempre para a página principal após tentar o cadastro
    return redirect(url_for('index'))


# Rota /update, renderiza update.html e processa o POST
@app.route('/update/<int:user_id>', methods=['GET', 'POST'])
def update(user_id):
    # Busca o usuário pelo ID ou retorna 404 se não encontrado
    try:
        user = User.query.get_or_404(user_id)
    except Exception as e:
        flash(f"Erro ao buscar usuário para atualização: {e}", 'danger')
        print(f"Erro ao buscar usuário {user_id} para atualização: {e}")
        return redirect(url_for('index'))

    # Processa a requisição POST (envio do formulário de atualização)
    if request.method == 'POST':
        # Obtém os dados do formulário
        new_name = request.form.get('nome') # Use 'nome' conforme o template HTML
        new_email = request.form.get('email') # Use 'email' conforme o template HTML
        new_password = request.form.get('new_password') # Use 'new_password' conforme o template HTML

        # --- Validação: Nome e Email são obrigatórios (seja na criação ou atualização) ---
        if not new_name or not new_email:
            flash('Nome e Email são obrigatórios.', 'warning')
            # Renderiza o template novamente, mantendo os dados do usuário original para pré-preencher
            return render_template('update.html', user=user, user_id=user_id)

        # --- Validação: Verificar se o novo email já existe, exceto para o usuário atual ---
        existing_user_with_email = User.query.filter_by(email=new_email).first()
        if existing_user_with_email and existing_user_with_email.id != user.id:
            flash(f'O email {new_email} já está cadastrado para outro usuário.', 'warning')
            print(f"Tentativa de atualização com email duplicado: {new_email} para usuário {user_id}")
            # Renderiza o template novamente com a mensagem de erro
            return render_template('update.html', user=user, user_id=user_id)

        # --- Nova Validação: Verificar se pelo menos um campo foi modificado ---
        # Compara os novos valores com os valores atuais do usuário
        is_modified = False
        if new_name != user.nome:
            is_modified = True
            user.nome = new_name # Atualiza o nome APENAS se foi modificado

        if new_email != user.email:
            is_modified = True
            user.email = new_email # Atualiza o email APENAS se foi modificado

        if new_password: # Se um novo password foi fornecido (campo não vazio)
            is_modified = True
            # Gera o hash da nova senha e atualiza
            user.senha = generate_password_hash(new_password)
            print(f"Nova senha fornecida para usuário {user_id}.")


        # Se nenhum campo foi modificado, flashear mensagem e re-renderizar o formulário
        if not is_modified:
            flash('Nenhuma alteração detectada. Por favor, modifique pelo menos um campo para atualizar.', 'info')
            print(f"Nenhuma alteração detectada para usuário {user_id}.")
            return render_template('update.html', user=user, user_id=user_id)

        # Se pelo menos um campo foi modificado, tentar salvar as alterações no banco de dados
        try:
            db.session.commit()
            flash('Usuário atualizado com sucesso!', 'success')
            print(f"Usuário {user_id} atualizado: Nome='{user.nome}', Email='{user.email}'")
            # Redireciona para a lista de usuários após o sucesso
            return redirect(url_for('index'))

        except Exception as e:
            db.session.rollback() # Reverte as alterações em caso de erro
            print(f"Erro ao salvar atualização do usuário {user_id}: {e}")
            flash(f"Erro ao atualizar usuário: {e}", 'danger')
            # Renderiza o template novamente em caso de erro no banco de dados
            return render_template('update.html', user=user, user_id=user_id)

    else:
        # Método GET: Apenas exibe o formulário de atualização preenchido com os dados atuais do usuário
        return render_template('update.html', user=user, user_id=user_id)


# Rota /delete permanece a mesma, processa a deleção (GET) e redireciona
@app.route('/delete/<int:user_id>')
def delete(user_id):
    
    try:
        user_to_delete = User.query.get_or_404(user_id)
    except Exception as e:
         flash(f"Erro ao buscar usuário para deletar: {e}", 'danger')
         print(f"Erro ao buscar usuário {user_id} para deletar: {e}")
         return redirect(url_for('index'))

    try:
        db.session.delete(user_to_delete)
        db.session.commit()
        flash('Usuário deletado com sucesso!', 'success')
        print(f"Usuário deletado: ID={user_id}")

    except Exception as e:
        db.session.rollback()
        print(f"Erro ao deletar usuário {user_id}: {e}")
        flash(f"Erro ao deletar usuário {user_id}: {e}", 'danger')

    return redirect(url_for('index')) # Redireciona de volta para a lista após deletar


# --- Bloco de Execução Principal ---
if __name__ == '__main__':
    try:
        with app.app_context():
            db.create_all()
            print("Conectado ao MySQL e verificando/criando tabelas...")
    except Exception as e:
        print(f"Erro fatal ao conectar ao MySQL ou criar tabelas: {e}")
 
    app.run(debug=True)