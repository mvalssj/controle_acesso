from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from datetime import datetime, timedelta
from app.models import Programacao, Unidade, ProgramacaoTipo, Equipamento, Entidade, EntidadePessoaFisica, db
from app.helpers.Intelbras import Usuarios, UserAPI, BiometricRegistration
from app.extensions import csrf  # Agora importa do extensions.py
import base64 # Adicione esta linha
from PIL import Image
import io
import sys
import os, re
import requests
import app

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from config import unidade, path_foto, username, password

class ProgramacaoController:
    def __init__(self):
        self.blueprint = Blueprint('programacao', __name__)
        self.equipamento_controller = app.equipamento_controller # Armazena a instância

        # Rota para listar todas as programações
        @self.blueprint.route('/programacoes', methods=['GET', 'POST'])
        @csrf.exempt  # Usa a instância csrf para desabilitar CSRF nessa rota
        def programacoes():
            # Obtém todas as programações do banco de dados
            programacoes = Programacao.query.all()
            programacao_tipo = ProgramacaoTipo.query.all()
            unidades = Unidade.query.all()
            # Renderiza a página de programações, passando a lista de programações como contexto
            return render_template('programacoes.html', programacoes=programacoes, unidades=unidades, programacao_tipo=programacao_tipo)

        # Rota para inserir uma nova programação
        @self.blueprint.route('/programacoes/novo', methods=['POST'])
        @csrf.exempt  # Usa a instância csrf para desabilitar CSRF nessa rota
        def novo_programacao():
            # Obtém os dados do formulário
            datahora_inicio = request.form.get('datahora_inicio')
            datahora_fim = request.form.get('datahora_fim')
            cavalo = request.form.get('cavalo')    
            carreta = request.form.get('carreta')  
            pessoa = request.form.get('pessoa')  
            cpf = request.form.get('cpf')  
            id_tipo = request.form.get('id_tipo')
            foto = request.form.get('foto')  # Adiciona a foto do formulário

            # Remove o prefixo "data:image/jpeg;base64," da variável foto, se existir
            if foto and foto.startswith('data:image/jpeg;base64,'):
                foto = foto[len('data:image/jpeg;base64,'):]

            # Envia os dados para o equipamento
            if foto:
                # print(foto)
                print(datahora_inicio)

                try:
                    api_data = {
                        "username": pessoa,
                        "password": '123',
                        "doors": [0],
                        "time_sections": [2],
                        "valid_from": datahora_inicio.replace(' ', '') + ":00",  # remove espaços e adiciona segundos
                        "valid_to": datahora_fim.replace(' ', '') + ":00",  # remove espaços e adiciona segundos
                        "foto": foto,
                        "cpf": cpf,
                        "criar": 1                   
                    }
                    # api_data = json.dumps(api_data)
                    print("Enviando os seguintes dados para o equipamento: ", api_data)
                    # Grave o valor da variável foto em um bloco de notas

                    headers = {
                        'Content-Type': 'application/json',
                        'Postman-Token': '<calculated when request is sent>',
                        'User-Agent': 'PostmanRuntime/7.42.0',
                        'Accept': '*/*',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Connection': 'keep-alive'
                    }

                    response = requests.post(url_for('programacao.api_cadastrar', _external=True), headers=headers, json=api_data)  # Envie api_data como JSON, sem convertê-lo em string

                    print("Resposta do equipamento: ", response.text)

                    if response.status_code == 200:
                        # Verifica se a resposta do equipamento indica sucesso
                        if response.json().get('success'):
                            # Cria um novo objeto Progracações
                            novo_programacao = Programacao(datahora_inicio=datahora_inicio, datahora_fim=datahora_fim, cavalo=cavalo, carreta=carreta, pessoa=pessoa, cpf=cpf, id_tipo=id_tipo)

                            # Adiciona o novo programação ao banco de dados
                            db.session.add(novo_programacao)
                            db.session.commit()

                            return redirect(url_for('programacao.programacoes'))
                        else:
                            return jsonify({'status': 'error', 'message': response.json().get('message')}), 500
                    else:
                        return jsonify({'status': 'error', 'message': 'Erro ao enviar dados para o equipamento. Código: {}'.format(response.status_code)}), 500
                except requests.exceptions.RequestException as e:
                    print(f"Erro ao enviar a requisição")
                    return jsonify({'status': 'error', 'message': f'Erro ao enviar dados para o equipamento'}), 500
                except Exception as e:
                    print(f"Erro desconhecido")
                    return jsonify({'status': 'error', 'message': f'Erro desconhecido'}), 500

            # Redireciona para a página de programacoes
            return redirect(url_for('programacao.programacoes'))
        
        # Rota para inserir uma nova programação veiculo
        @self.blueprint.route('/webhook/programacao/veiculo', methods=['POST'])
        @csrf.exempt  # Usa a instância csrf para desabilitar CSRF nessa rota
        def novo_programacao_veiculo():
            # Obtém os dados do formulário
            data = request.get_json()
            print(data)
            
            # Valida se todos os campos obrigatórios estão preenchidos
            if not all([data.get('datahora_inicio'), data.get('datahora_fim'), data.get('veiculo'), data.get('pessoa')]):
                campos_faltantes = []
                if not data.get('datahora_inicio'):
                    campos_faltantes.append('datahora_inicio')
                if not data.get('datahora_fim'):
                    campos_faltantes.append('datahora_fim')
                if not data.get('veiculo'):
                    campos_faltantes.append('veiculo')
                if not data.get('pessoa'):
                    campos_faltantes.append('pessoa')
                return jsonify({'status': 'error', 'message': f'Os seguintes campos estão faltando: {", ".join(campos_faltantes)}'}), 400

            # Cria um novo objeto Programacao
            novo_programacao = Programacao(
                datahora_inicio=data.get('datahora_inicio'),
                datahora_fim=data.get('datahora_fim'),
                cavalo=data.get('veiculo').get('cavalo').get('placa') or '',  # Se o campo 'placa' for vazio, grava como string vazia
                carreta=data.get('veiculo').get('carreta').get('placa') or '',  # Se o campo 'placa' for vazio, grava como string vazia
                pessoa=data.get('pessoa').get('nome') or '',  # Se o campo 'nome' for vazio, grava como string vazia
                cpf=data.get('pessoa').get('pessoa_fisica').get('cpf') or '',  # Se o campo 'cpf' for vazio, grava como string vazia
                id_tipo=data.get('id_tipo')
            )

            # Verifica se algum campo veio com string vazia
            campos_vazios = []
            if novo_programacao.cavalo == '':
                campos_vazios.append('cavalo')
            if novo_programacao.carreta == '':
                campos_vazios.append('carreta')
            if novo_programacao.pessoa == '':
                campos_vazios.append('pessoa')
            if novo_programacao.cpf == '':
                campos_vazios.append('cpf')

            # Adiciona a nova programação ao banco de dados
            db.session.add(novo_programacao)
            db.session.commit()

            # Retorna uma resposta de sucesso ou com os campos vazios
            if campos_vazios:
                return jsonify({'status': 'warning', 'message': 'Programação recebida com sucesso!', 'campos_vazios': campos_vazios})
            else:
                return jsonify({'status': 'success', 'message': 'Programação recebida com sucesso!'})

        # Rota para inserir uma nova programação pessoas
        @self.blueprint.route('/webhook/programacao/pessoa', methods=['POST'])
        @csrf.exempt  # Usa a instância csrf para desabilitar CSRF nessa rota
        def novo_programacao_pessoa():
            # Obtém os dados do formulário
            data = request.get_json()
            print(data)
            
            # Valida se todos os campos obrigatórios estão preenchidos
            if not all([data.get('datahora_inicio'), data.get('datahora_fim'), data.get('pessoa')]):
                campos_faltantes = []
                if not data.get('datahora_inicio'):
                    campos_faltantes.append('datahora_inicio')
                if not data.get('datahora_fim'):
                    campos_faltantes.append('datahora_fim')                
                if not data.get('pessoa'):
                    campos_faltantes.append('pessoa')
                return jsonify({'status': 'error', 'message': f'Os seguintes campos estão faltando: {", ".join(campos_faltantes)}'}), 400

            # Cria um novo objeto Programacao
            novo_programacao = Programacao(
                datahora_inicio=data.get('datahora_inicio'),
                datahora_fim=data.get('datahora_fim'),
                pessoa=data.get('pessoa').get('nome') or '',  # Se o campo 'nome' for vazio, grava como string vazia
                cpf=data.get('pessoa').get('pessoa_fisica').get('cpf') or '',  # Se o campo 'cpf' for vazio, grava como string vazia
                id_tipo=data.get('id_tipo')
            )

            # Verifica se algum campo veio com string vazia
            campos_vazios = []            
            if novo_programacao.pessoa == '':
                campos_vazios.append('pessoa')
            if novo_programacao.cpf == '':
                campos_vazios.append('cpf')

            # Adiciona a nova programação ao banco de dados
            db.session.add(novo_programacao)
            db.session.commit()

            # Retorna uma resposta de sucesso ou com os campos vazios
            if campos_vazios:
                return jsonify({'status': 'warning', 'message': 'Programação recebida com sucesso!', 'campos_vazios': campos_vazios})
            else:
                return jsonify({'status': 'success', 'message': 'Programação recebida com sucesso!'})

        # Rota para atualizar uma programação
        @self.blueprint.route('/programacoes/<int:id>/editar', methods=['GET', 'POST'])
        @csrf.exempt  # Usa a instância csrf para desabilitar CSRF nessa rota
        def editar_programacao(id):

            # Captura o ip das biometrias
            ips_entrada, ips_saida = self.equipamento_controller.get_equipamento_id(unidade)
            
            # Itera sobre os IPs de entrada e saída
            for ip_entrada in ips_entrada:
                for ip_saida in ips_saida:
                    print('IP Entrada:', ip_entrada)
                    print('IP Saída:', ip_saida)
                    device_ip_in = ip_entrada
                    device_ip_out = ip_saida
            # Captura o ip das biometrias

                    # Obtém a programação a ser editada
                    print("ID PROGRAMAÇÂO: ", id)
                    programacao = Programacao.query.get_or_404(id)

                    # Se o método for POST, atualiza a programação
                    if request.method == 'POST':
                        # Obtém os dados do formulário
                        datahora_inicio = request.form.get('datahora_inicio') + ":00"
                        datahora_fim = request.form.get('datahora_fim') + ":00"
                        cavalo = request.form.get('cavalo')
                        carreta = request.form.get('carreta')
                        pessoa = request.form.get('pessoa')
                        cpf_atual = request.form.get('cpf_atual')
                        cpf = request.form.get('cpf')
                        id_tipo = request.form.get('id_tipo')
                        foto = request.form.get('foto')
                        id_user = request.form.get('id_equipamento')

                        # Remove o prefixo "data:image/jpeg;base64," da variável foto, se existir
                        if foto and foto.startswith('data:image/jpeg;base64,'):
                            foto = foto[len('data:image/jpeg;base64,'):]
                            # print(foto)
                            # Remove a foto atual para passar a nova
                            url_foto = f"http://{device_ip_in}/cgi-bin/AccessFace.cgi?action=removeMulti&UserIDList[0]={id_user}"
                            digest_auth = requests.auth.HTTPDigestAuth(username, password)
                            rval = requests.get(url_foto, auth=digest_auth, stream=True, timeout=20, verify=False)
                            print("Foto removida: ",rval)
                        
                        if cpf:
                            # Remove a cpf atual para passar novo
                            url_cpf = f"http://{device_ip_in}/cgi-bin/AccessCard.cgi?action=removeMulti&CardNoList[0]={cpf_atual}"
                            print("URL CPF: ", url_cpf)
                            digest_auth = requests.auth.HTTPDigestAuth(username, password)
                            rval = requests.get(url_cpf, auth=digest_auth, stream=True, timeout=20, verify=False)
                            print("CPF removido: ",rval)

                        # Atualiza os dados da programação
                        programacao.datahora_inicio = datahora_inicio
                        programacao.datahora_fim = datahora_fim
                        programacao.cavalo = cavalo
                        programacao.carreta = carreta
                        programacao.pessoa = pessoa
                        programacao.cpf = cpf
                        programacao.id_tipo = id_tipo

                        # Salva as alterações no banco de dados
                        db.session.commit()

                        headers = {
                        'Content-Type': 'application/json',
                        'Postman-Token': '<calculated when request is sent>',
                        'User-Agent': 'PostmanRuntime/7.42.0',
                        'Accept': '*/*',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Connection': 'keep-alive'
                        }

                        # Cria o json para editar no equipamento
                        json_equipamento = {
                            "username": pessoa,
                            "password": "142114",
                            "doors": [0],
                            "time_sections": [2],
                            "valid_from": datahora_inicio,
                            "valid_to": datahora_fim,
                            "id_user": id_user,
                            "cpf": cpf,
                            "foto": foto,
                            "edit": 1
                        }
                        
                        requests.post(url_for('programacao.api_cadastrar', _external=True), headers=headers, json=json_equipamento)

                        # Redireciona para a página de programações
                        return redirect(url_for('programacao.programacoes'))

                    # Se o método for GET, renderiza a página de edição
                    return render_template('editar_programacao.html', programacao=programacao)

        # Rota para apagar uma programação
        @self.blueprint.route('/programacoes/<int:id>/apagar', methods=['POST'])
        def apagar_programacao(id):
            # Obtém a programação a ser apagada
            programacao = Programacao.query.get_or_404(id)

            # Remove a programação do banco de dados
            db.session.delete(programacao)
            db.session.commit()

            # Redireciona para a página de programações após a exclusão
            return redirect(url_for('programacao.programacoes'))

        # Rota para buscar programação por CPF
        @self.blueprint.route('/programacoes/cpf', methods=['POST'])
        @csrf.exempt  # Usa a instância csrf para desabilitar CSRF nessa rota
        def buscar_programacao_por_cpf():
            # Obtém o CPF enviado via JSON
            data = request.get_json()
            cpf = data.get('cpf')

            # Busca as programações no banco de dados que correspondem ao CPF
            programacoes = Programacao.query.filter_by(cpf=cpf).all()

            # Obtém a data/hora atual
            agora = datetime.now()

            # Verifica se há programações no intervalo da data atual
            programacoes_validas = [prog for prog in programacoes if prog.datahora_inicio <= agora <= prog.datahora_fim]

            # Se encontrar programações dentro do intervalo, retorna a primeira encontrada
            if programacoes_validas:
                programacao = programacoes_validas  # Armazena todas as programações válidas
                programacao_unica = programacao[0] if programacao else None  # Mantém a primeira programação, se existir
                return jsonify({
                    'status': 'success',
                    'programacao': {
                        'id': programacao_unica.id if programacao_unica else None,
                        'pessoa': programacao_unica.pessoa if programacao_unica else None,
                        'cpf': programacao_unica.cpf if programacao_unica else None,
                        'cavalo': programacao_unica.cavalo if programacao_unica else None,
                        'carreta': programacao_unica.carreta if programacao_unica else None,
                        'datahora_inicio': programacao_unica.datahora_inicio.strftime('%Y-%m-%dT%H:%M') if programacao_unica else None,
                        'datahora_fim': programacao_unica.datahora_fim.strftime('%Y-%m-%dT%H:%M') if programacao_unica else None,
                    },
                    'programacoes_validas': [
                        {
                            'id': prog.id,
                            'pessoa': prog.pessoa,
                            'cpf': prog.cpf,
                            'cavalo': prog.cavalo,
                            'carreta': prog.carreta,
                            'datahora_inicio': prog.datahora_inicio.strftime('%Y-%m-%dT%H:%M'),
                            'datahora_fim': prog.datahora_fim.strftime('%Y-%m-%dT%H:%M'),
                        } for prog in programacao  # Itera sobre todas as programações válidas
                    ]
                })
            
            # Se não encontrar nenhuma programação válida, retorna uma mensagem de erro
            else:
                return jsonify({'status': 'error', 'message': 'Nenhuma programação ativa no intervalo de tempo atual.'}), 404

        # Rota para buscar informação no equipamento por CPF
        @self.blueprint.route('/buscar/equipamento', methods=['POST'])
        @csrf.exempt  # Usa a instância csrf para desabilitar CSRF nessa rota
        def buscar_equipamento():

            # Captura o ip das biometrias
            ips_entrada, ips_saida = self.equipamento_controller.get_equipamento_id(unidade)
            
            # Obtém o CPF enviado via JSON
            data = request.get_json()
            cpf = data.get('cpf')
            print("Entrou em Buscar Equipamento", cpf)
            device_ip_in = '192.168.9.11'

            if not cpf:
                return jsonify({'status': 'error', 'message': 'CPF não fornecido.'}), 400

            # URL do equipamento com o CPF
            url_id = f"http://{device_ip_in}/cgi-bin/AccessCard.cgi?action=list&CardNoList[0]={cpf}"

            try:
                # Autenticação HTTP Digest
                digest_auth = requests.auth.HTTPDigestAuth(username, password)
                
                # Faz a requisição ao equipamento para capturar o id
                response_id = requests.get(url_id, auth=digest_auth, stream=True, timeout=20, verify=False)
                
                # Verifica se a requisição foi bem sucedida
                if response_id.status_code == 200:
                    # Extrair o UserID da resposta
                    user_id = None
                    for line in response_id.text.splitlines():
                        if line.startswith("Cards[0].UserID="):  # Corrigido para "Cards"
                            user_id = line.split("=")[1]
                            break
                                        
                    if user_id:
                        print(f"UserID: {user_id}")
                    else:
                        print("UserID não encontrado na resposta.")

                    url_foto = f"http://{device_ip_in}/cgi-bin/AccessFace.cgi?action=list&UserIDList[0]={user_id}"

                    # Faz a requisição ao equipamento para capturar a foto
                    response_foto = requests.get(url_foto, auth=digest_auth, stream=True, timeout=20, verify=False)

                    # Extrair a string da resposta
                    response_text = response_foto.text
                    
                    # Encontrar e extrair a string base64
                    photo_data_prefix = "FaceDataList[0].PhotoData[0]="
                    start_index = response_text.find(photo_data_prefix) + len(photo_data_prefix)
                    end_index = response_text.find("FaceDataList[0].UserID")

                    # Obter a parte relevante da string base64
                    photo_base64 = response_text[start_index:end_index].strip()

                    # Limpar a string base64 de caracteres de nova linha
                    clean_photo_base64 = photo_base64.replace("\r", "").replace("\n", "")

                    # Verificar se a string base64 é válida
                    try:
                        # Decodificar para verificar a validade
                        image_data = base64.b64decode(clean_photo_base64)
                        print("A string base64 foi decodificada com sucesso.")
                    except Exception as e:
                        print("Erro ao decodificar a string base64:", e)

                    # Codificar os dados da imagem (caso necessário para enviar ao frontend)
                    encoded_image = base64.b64encode(image_data).decode('utf-8')
                    
                    # Retornar a resposta para o frontend
                    return jsonify({'status': 'success', 'data': response_id.text, 'id': user_id, 'foto': encoded_image})

                else:
                    return jsonify({'status': 'error', 'message': 'Erro ao buscar dados do equipamento.', 'code': response_id.status_code}), 500
            except requests.exceptions.RequestException as e:
                return jsonify({'status': 'error', 'message': f'Requisição falhou: {str(e)}'}), 500

        @self.blueprint.route('/api/cadastrar', methods=['POST'])
        @csrf.exempt
        def api_cadastrar():
            if not request.is_json:
                return jsonify(success=False, message='Requisição inválida.')
                
            # Captura o ip das biometrias
            ips_entrada, ips_saida = self.equipamento_controller.get_equipamento_id(unidade)
            data = request.get_json()
            
            # Define o IP e URL baseado na presença de device_ip_out
            if data.get('device_ip_out'):
                dispositivos = ips_saida
            else:
                dispositivos = ips_entrada

            # Processa cada dispositivo uma única vez 
            for device_ip in dispositivos:
                print('IP do dispositivo:', device_ip)
                current_device_ip = device_ip
                current_base_url = f"http://{current_device_ip}/cgi-bin/AccessUser.cgi"

                # Determina o ID do usuário
                if data.get('criar'):
                    url = f"http://{ips_entrada[0]}/cgi-bin/recordFinder.cgi?action=doSeekFind&name=AccessControlCard"
                    request_usuarios = Usuarios(url, username, password)
                    usuarios = request_usuarios.obter_usuarios()
                    maior_userid = request_usuarios.obter_maior_userid(usuarios)
                    
                    # Verifica se é a primeira iteração do loop
                    if current_device_ip == dispositivos[0]:
                        id_user = int(maior_userid["UserID"]) + 1 if maior_userid else 1
                    else:
                        id_user = int(maior_userid["UserID"]) if maior_userid else 1
                    
                    # verifica se o já está na controladora
                    cpf = data.get('cpf') or data.get('card_no') 
                    url = f"http://{ips_entrada[0]}/cgi-bin/AccessCard.cgi?action=list&CardNoList[0]={cpf}"
                    digest_auth = requests.auth.HTTPDigestAuth(username, password)
                    rval = requests.get(url, auth=digest_auth, stream=True, timeout=20, verify=False)
                    # print('############# Cadastro cpf:',rval.text)
                    user_id = None
                    match = re.search(r'UserID=(\d+)', rval.text)
                    if match:
                        user_id = match.group(1)

                    print('UserID:', user_id)
                    if user_id != None:
                        id_user = user_id
                    # verifica se o já está na controladora

                else:    
                    id_user = data['id_user']

                # Dados do usuário
                user_data = {
                    "UserList": [{
                        "UserID": str(id_user),
                        "UserName": data['username'],
                        "UserType": 0,
                        "Authority": 2,
                        "Password": data['password'],
                        "Doors": [int(door) for door in data['doors']],
                        "TimeSections": [int(time_section) for time_section in data['time_sections']],
                        "ValidFrom": data['valid_from'].replace('T', ' '),
                        "ValidTo": data['valid_to'].replace('T', ' ')
                    }]
                }

                # Criação da instância da API e envio dos dados do usuário
                api = UserAPI(current_base_url, username, password)
                status_code, response = api.send_user("insertMulti", user_data)  

                # if status_code == 200:
                if True:
                    print('ENTROU PARA CADASTRAR CPF: ###########################',id_user)
                    # Cadastra o CPF ou CardNo
                    card_data = {
                        "CardList": [{
                            "UserID": str(id_user),
                            "CardNo": data.get('cpf') or data.get('card_no'),
                            "CardType": "0",
                            "CardStatus": "0"
                        }]
                    }

                    card_url = f"http://{current_device_ip}/cgi-bin/AccessCard.cgi?action=insertMulti"
                    card_api = UserAPI(card_url, username, password)
                    card_status_code, card_response_content = card_api.send_user("insertMulti", card_data)
                    
                    print(card_response_content);

                    if card_status_code == 200:
                        # Processa a foto da biometria
                        foto_base64 = data.get('foto')
                        if foto_base64:
                            try:
                                foto_bytes = base64.b64decode(foto_base64)
                                imagem = Image.open(io.BytesIO(foto_bytes))
                                image_path = os.path.join(path_foto, 'foto.jpg')
                                imagem.save(image_path)
                                
                                biometric_registration = BiometricRegistration(current_device_ip, username, password)
                                biometric_registration.register_face(str(id_user), image_path)
                                print(f'Usuário cadastrado com sucesso no dispositivo {current_device_ip}')
                            except Exception as e:
                                print(f"Erro ao processar biometria no dispositivo {current_device_ip}: {str(e)}")
                                # return jsonify(success=False, message=f"Erro ao decodificar a biometria: {str(e)}")
                    else:
                        print(f'Erro ao cadastrar CPF/CardNo no dispositivo {current_device_ip}')
                        # return jsonify(success=False, message=f'Erro ao cadastrar CPF/CardNo no dispositivo {current_device_ip}')
                else:
                    print(f'Erro ao cadastrar usuário no dispositivo {current_device_ip}')
                    # return jsonify(success=False, message=f'Erro ao cadastrar usuário no dispositivo {current_device_ip}')

            return jsonify(success=True, message='Cadastro realizado com sucesso em todos os dispositivos!')
                
        @self.blueprint.route('/cadastro/pessoa', methods=['POST'])
        @csrf.exempt
        def cadastro_pessoa():

                    try:
                        data = request.get_json()

                        # Lista de campos obrigatórios de Entidade e EntidadePessoaFisica
                        required_fields_entidade = ['nome', 'natureza', 'unidade_negocio', 'ativo', 'sigla', 'fornecedor', 'cliente', 'colaborador', 'terceiro', 'motorista', 'transportador', 'salina', 'agencia_maritima', 'operador', 'armador', 'representante', 'id_entidade_matriz', 'id_entidade_representada']
                        required_fields_pessoa_fisica = ['id_pais', 'nome', 'cpf_passaporte', 'cnh', 'rg']

                        # Validação dos campos de Entidade
                        for field in required_fields_entidade:
                            if field not in data or not data[field]:  # Verifica se o campo existe e não é vazio
                                return jsonify({'status': 'error', 'message': f'O campo {field} (Entidade) é obrigatório.'}), 400

                        # Validação dos campos de EntidadePessoaFisica
                        for field in required_fields_pessoa_fisica:
                            if field not in data or not data[field]:
                                return jsonify({'status': 'error', 'message': f'O campo {field} (Pessoa Física) é obrigatório.'}), 400

                        try:
                            # Criação da Entidade
                            nova_entidade = Entidade(**{field: data.get(field) for field in required_fields_entidade})
                            db.session.add(nova_entidade)
                            db.session.flush()

                            # Criação da EntidadePessoaFisica
                            nova_pessoa_fisica = EntidadePessoaFisica(id_entidade=nova_entidade.id, **{field: data.get(field) for field in required_fields_pessoa_fisica})
                            db.session.add(nova_pessoa_fisica)
                            db.session.commit()

                            return jsonify({'status': 'success', 'message': 'Entidade e Pessoa Física criadas com sucesso!'}), 201

                        except Exception as e:
                            db.session.rollback()
                            print(f"Erro ao criar entidade/pessoa física: {e}")
                            return jsonify({'status': 'error', 'message': 'Erro ao criar entidade/pessoa física.'}), 500

                    except Exception as e:
                        print(f"Erro ao processar requisição: {e}")
                        return jsonify({'status': 'error', 'message': 'Erro ao processar requisição.'}), 500
