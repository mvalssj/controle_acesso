from app.controllers.EquipamentoController import EquipamentoController  # Importa o blueprint do EquipamentoController
from app.controllers.UnidadeController import UnidadeController  # Importa o blueprint do UnidadeController
from app.controllers.LocalAcessoController import LocalAcessoController  # Importa o blueprint do LocalAcessoController
from app.controllers.EventoController import EventoController  # Importa o blueprint do EventoController
from app.controllers.EntidadeController import EntidadeController  # Importa o blueprint do EntidadeController
from app.controllers.ProgramacaoController import ProgramacaoController  # Importa o blueprint do ProgramacaoController
from app.controllers.OperacionalController import OperacionalController  # Importa o blueprint do OperacionalController
from app.controllers.DashboardController import DashboardController  # Importa o blueprint do DashboardController
from app.controllers.AuthController import AuthController  # Importa o blueprint do AuthController
from flask import session, Flask, render_template, redirect, url_for, request, send_from_directory
from flask_session import Session  # Importe a classe Session
from app.models import Unidade, db  # Importa a instância de SQLAlchemy do models.py
from app.extensions import csrf  # Importa a instância do CSRFProtect do extensions.py
from functools import wraps
from flask import jsonify
import subprocess
import requests # Importa a biblioteca requests
import time
import threading
from PIL import Image

# Cria a aplicação Flask
app = Flask(__name__)

# Inicializa a proteção CSRF global
csrf.init_app(app)  # Usa a instância csrf de extensions

# Configuração da sessão
app.config['SESSION_TYPE'] = 'filesystem'  # Utilize o tipo filesystem para armazenar a sessão localmente
app.config['SESSION_PERMANENT'] = False  # Define se a sessão expira quando o navegador é fechado
app.config['SESSION_COOKIE_NAME'] = 'ipass_session'  # Nome do cookie da sessão
app.secret_key = 'Krrjb39142114@@@'  # Chave secreta para encriptar a sessão (importante para segurança)

Session(app)  # Inicializa a extensão Session

# Configuração do banco de dados
app.config.from_object('config.Config')

# Inicializa o SQLAlchemy com o aplicativo Flask
db.init_app(app)

# Registrar o blueprint dos controllers
equipamento_controller = EquipamentoController()
app.register_blueprint(equipamento_controller.blueprint)

# Registrar o blueprint dos controllers
entidade_controller = EntidadeController()
app.register_blueprint(entidade_controller.blueprint)

unidade_controller = UnidadeController()
app.register_blueprint(unidade_controller.blueprint)

local_acesso_controller = LocalAcessoController()
app.register_blueprint(local_acesso_controller.blueprint)

evento_controller = EventoController()
app.register_blueprint(evento_controller.blueprint)

programacao_controller = ProgramacaoController()
app.register_blueprint(programacao_controller.blueprint)

operacional_controller = OperacionalController()
app.register_blueprint(operacional_controller.blueprint)

dashboard_controller = DashboardController()
app.register_blueprint(dashboard_controller.blueprint)

auth_controller = AuthController()
app.register_blueprint(auth_controller.blueprint)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/autenticar', methods=['POST'])
@csrf.exempt  # Usa a instância csrf para desabilitar CSRF nessa rota
def autenticar():
    # Captura os dados do POST
    data = request.form
    # Imprime os dados no terminal
    print(f"Tentativa de autenticação com username: {data.get('username')}")
    
    # Verifica se o usuário e senha são válidos
    if data.get('username') == 'teste' and data.get('password') == 'teste':
        # Define o usuário na sessão após a autenticação
        session['usuario'] = data.get('username')
        print("Usuário autenticado com sucesso.")
        return redirect(url_for('home'))
    else:
        # Redireciona para a página de login com erro
        print("Autenticação falhou: Usuário ou senha inválidos.")
        return render_template('index.html', error='Usuário ou senha inválidos.')

@app.route('/logout')
def logout():
    session.pop('usuario', None)  # Remove o usuário da sessão
    return redirect(url_for('index'))  # Redireciona para a página de login
    
@app.before_request
def verificar_login():
    # Lista de rotas que não precisam de autenticação
    rotas_publicas = ['index', 'autenticar', 'static', 'logout', 'home', 'evento.novo_evento', 'programacao.buscar_programacao_por_cpf', 'programacao.api_cadastrar', 'evento.checa_placas', 'programacao.novo_programacao_veiculo', 'programacao.buscar_varias_programacoes_por_cpf']  # Inclua todas as rotas públicas

    print('Pagina requisitada: ',request.endpoint)
    # Verifica se o endpoint atual não é uma das rotas públicas e se o usuário não está autenticado
    if request.endpoint not in rotas_publicas and 'usuario' not in session:
        print("Usuário não autenticado, redirecionando para a página de login.")
        return render_template('index.html', error='Você precisa estar logado para acessar esta página.') # Retorna o template index.html com a mensagem de erro

@app.route('/home', methods=['GET'])
def home():
    unidades = Unidade.query.all()
    return render_template('home.html', unidades=unidades)

@app.route('/placa_frontal', methods=['GET'])  # Corrigido para '/placa.txt'
def serve_placa():
    # Abre o arquivo 'placa.txt' no modo de leitura
    with open('app\\services\\lpr\\placa_frontal.txt', 'r') as file:
        # Lê o conteúdo do arquivo
        conteudo = file.read()
    # Retorna o conteúdo do arquivo como resposta
    return conteudo

@app.route('/placas_balanca', methods=['GET'])
def serve_placa_balanca():
    try:
        with open('app\\services\\lpr\\placa_traseira_balanca.txt', 'r') as file_traseira, open('app\\services\\lpr\\placa_frontal_balanca.txt', 'r') as file_frontal:
            conteudo_traseira = file_traseira.read()
            conteudo_frontal = file_frontal.read()
        # Retorna o conteúdo dos arquivos como um JSON
        return jsonify({
            "placa_traseira": conteudo_traseira,
            "placa_frontal": conteudo_frontal
        })
    except FileNotFoundError:
        return jsonify({"error": "Um ou ambos os arquivos de placa não foram encontrados."}), 500

@app.route('/ajuda')
def serve_ajuda():
    return send_from_directory('static/files', 'ajuda.pdf')

@app.route('/new_foto_placa_frontal', methods=['GET'])
def new_foto_placa_frontal():
    # Importe a biblioteca subprocess
    import subprocess

    try:
        # Executa o script lpr.py
        subprocess.run(["python", "app\\services\\lpr\\lpr_camera.py"], check=True) # check=True levanta exceção se o script falhar
        return "Nova foto da placa frontal capturada e processada com sucesso!", 200
    except subprocess.CalledProcessError as e:
        print(f"Erro ao executar lpr_camera.py: {e}")  # Imprime o erro para debug
        print(f"Saída padrão: {e.stdout.decode()}") # Imprime a saida padrão do comando
        print(f"Saída de erro: {e.stderr.decode()}") # Imprime a saida de erro do comando
        return "Erro ao capturar a foto da placa frontal.", 500 # Retorna erro 500 para o cliente
    except FileNotFoundError:
        return "Script lpr_camera.py não encontrado.", 500 # Retorna erro 500 para o cliente
    
@app.route('/new_foto_placas_balanca', methods=['GET'])
def new_foto_placas_balanca():

    try:
        for tipo_placa in ["balanca_frontal", "balanca_traseira"]:
            # Executa o script lpr.py com o parâmetro tipo_placa
            subprocess.run(["python", "app\\services\\lpr\\lpr_camera.py", tipo_placa], check=True, capture_output=True)
            print(f"Nova foto da placa {tipo_placa} da balança capturada e processada com sucesso!")

        # Executa o request após o loop que processa as fotos
        try:
            resposta = requests.get('http://127.0.0.1/checa_placas', params={'tipo': 1}, timeout=5)
            resposta.raise_for_status()  # Lança uma exceção para códigos de status HTTP de erro (4xx ou 5xx)
            print('Resposta do request /checa_placas:', resposta.text)
            print("###### Request /checa_placas executado com sucesso ######")
            return "Novas fotos das placas da balança capturadas e processadas com sucesso! Request /checa_placas executado.", 200

        except requests.exceptions.RequestException as e:
            print(f"Erro ao executar o request /checa_placas: {e}")
            return "Erro ao executar o request /checa_placas após capturar as fotos.", 500


    except subprocess.CalledProcessError as e:
        print(f"Erro ao executar lpr.py: {e}")
        print(f"Saída padrão: {e.stdout.decode()}")
        print(f"Saída de erro: {e.stderr.decode()}")
        return "Erro ao capturar a foto da placa da balança.", 500
    except FileNotFoundError:
        return "Script lpr.py não encontrado.", 500

@app.route('/placa_manual', methods=['POST'])
def placa_manual():
    try:
        placa = request.form.get('placa') # Obtém a placa enviada via POST
        if not placa:
            return "Placa não fornecida.", 400 # Retorna erro 400 se a placa não for fornecida

        with open('C:\\controle_acesso\\app\\services\\lpr\\placa_frontal.txt', 'w') as f:
            f.write(placa)
        return "Placa gravada com sucesso!", 200

    except Exception as e:
        print(f"Erro ao gravar a placa: {e}") # Imprime o erro para debug
        return "Erro ao gravar a placa.", 500

@app.route('/placa_manual_balanca', methods=['POST'])
def placa_manual_balanca():
    try:
        placa_frontal = request.form.get('placa_frontal')
        placa_traseira = request.form.get('placa_traseira')

        if not placa_frontal or not placa_traseira:
            return "Placas não fornecidas.", 400

        with open('app\\services\\lpr\\placa_frontal_balanca.txt', 'w') as f:
            f.write(placa_frontal)

        with open('app\\services\\lpr\\placa_traseira_balanca.txt', 'w') as f:
            f.write(placa_traseira)

        def valida():
            time.sleep(3) # Aguarda 3 segundos antes de fazer a requisição
            try:

                resposta = requests.get('http://127.0.0.1/checa_placas', params={'tipo': 1}, timeout=5)

                resposta.raise_for_status() # Lança uma exceção para códigos de status HTTP de erro (4xx ou 5xx)
                print('Resposta: ', resposta.text) # Imprime o conteúdo da resposta
                print("###### Placas Validadas ######")

            except requests.exceptions.RequestException as e:
                print(f"Erro ao checar placas: {e}")

        # Inicia a checagem de placas em uma thread separada
        threading.Thread(target=valida).start()

        return "Placas gravadas com sucesso! A validação está sendo processada em segundo plano.", 200

    except Exception as e:
        print(f"Erro ao gravar as placas: {e}")
        return "Erro ao gravar as placas.", 500

@app.route('/placa_frontal_manual_balanca', methods=['POST'])
def placa_frontal_manual_balanca():
    try:
        placa_frontal = request.form.get('placa_frontal')

        if not placa_frontal:
            return "Placas não fornecidas.", 400

        with open('app\\services\\lpr\\placa_frontal_balanca.txt', 'w') as f:
            f.write(placa_frontal)

        def valida():
            time.sleep(3) # Aguarda 3 segundos antes de fazer a requisição
            try:

                resposta = requests.get('http://127.0.0.1/checa_placas', params={'tipo': 1}, timeout=5)

                resposta.raise_for_status() # Lança uma exceção para códigos de status HTTP de erro (4xx ou 5xx)
                print('Resposta: ', resposta.text) # Imprime o conteúdo da resposta
                print("###### Placas Validadas ######")

            except requests.exceptions.RequestException as e:
                print(f"Erro ao checar placas: {e}")

        # Inicia a checagem de placas em uma thread separada
        threading.Thread(target=valida).start()

        return "Placas gravadas com sucesso! A validação está sendo processada em segundo plano.", 200

    except Exception as e:
        print(f"Erro ao gravar as placa: {e}")
        return "Erro ao gravar as placa.", 500

@app.route('/placa_traseira_manual_balanca', methods=['POST'])
def placa_traseira_manual_balanca():
    try:
        placa_traseira = request.form.get('placa_traseira')

        if not placa_traseira:
            return "Placas não fornecidas.", 400

        with open('app\\services\\lpr\\placa_traseira_balanca.txt', 'w') as f:
            f.write(placa_traseira)

        def valida():
            time.sleep(3) # Aguarda 3 segundos antes de fazer a requisição
            try:

                resposta = requests.get('http://127.0.0.1/checa_placas', params={'tipo': 1}, timeout=5)

                resposta.raise_for_status() # Lança uma exceção para códigos de status HTTP de erro (4xx ou 5xx)
                print('Resposta: ', resposta.text) # Imprime o conteúdo da resposta
                print("###### Placas Validadas ######")

            except requests.exceptions.RequestException as e:
                print(f"Erro ao checar placas: {e}")

        # Inicia a checagem de placas em uma thread separada
        threading.Thread(target=valida).start()

        return "Placas gravadas com sucesso! A validação está sendo processada em segundo plano.", 200

    except Exception as e:
        print(f"Erro ao gravar as placas: {e}")
        return "Erro ao gravar as placas.", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False, port=80)

