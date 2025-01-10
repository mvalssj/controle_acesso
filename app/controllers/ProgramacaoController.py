from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from datetime import datetime, timedelta
from app.models import Programacao, Unidade, ProgramacaoTipo, Equipamento, Entidade, EntidadePessoaFisica, db
from app.helpers.Intelbras import Usuarios, UserAPI, BiometricRegistration
from app.extensions import csrf  # Agora importa do extensions.py
import base64 # Adicione esta linha
from PIL import Image
import io
import sys
import os
import requests
import app

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from config import unidade, base_url_in, base_url_out, path_foto, username, password

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
                        "cpf": cpf                   
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
                programacao = programacoes_validas[0]  # Aqui você pode ajustar para retornar mais de uma, se necessário
                return jsonify({
                    'status': 'success',
                    'programacao': {
                        'pessoa': programacao.pessoa,
                        'cpf': programacao.cpf,
                        'cavalo': programacao.cavalo,
                        'carreta': programacao.carreta,
                        'datahora_inicio': programacao.datahora_inicio.strftime('%Y-%m-%dT%H:%M'),
                        'datahora_fim': programacao.datahora_fim.strftime('%Y-%m-%dT%H:%M')
                    }
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
            
            # Itera sobre os IPs de entrada e saída
            for ip_entrada in ips_entrada:
                for ip_saida in ips_saida:
                    print('IP Entrada:', ip_entrada)
                    print('IP Saída:', ip_saida)
                    device_ip_in = ip_entrada
                    device_ip_out = ip_saida
            # Captura o ip das biometrias
            direcao = data.get('direcao')
            print('#### Direção:', direcao)

            if direcao == 'IN':
                device_ip = device_ip_in
            elif direcao == 'OUT':
                device_ip = device_ip_out
            else:
                return jsonify({'status': 'error', 'message': 'Direção inválida.'}), 400

            # Obtém o CPF enviado via JSON
            data = request.get_json()
            cpf = data.get('cpf')
            print("Entrou em Buscar Equipamento", cpf)

            if not cpf:
                return jsonify({'status': 'error', 'message': 'CPF não fornecido.'}), 400

            # URL do equipamento com o CPF
            url_id = f"http://{device_ip}/cgi-bin/AccessCard.cgi?action=list&CardNoList[0]={cpf}"

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

                    url_foto = f"http://{device_ip}/cgi-bin/AccessFace.cgi?action=list&UserIDList[0]={user_id}"

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

                    # Exibir a string base64 limpa no terminal
                    # print("String Base64 da Foto:", clean_photo_base64)

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
        # @token_required  # Protege a rota com o token JWT
        @csrf.exempt  # Usa a instância csrf para desabilitar CSRF nessa rota
        def api_cadastrar():
            
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

                    print("Entrou na api_cadastrar: ")
                    # print(f"Tipo de data recebido: {type(data)}")
                    if request.is_json:
                                                    
                        data = request.get_json()
                    
                        # Usa 'device_ip_out' se estiver presente nos dados, senão usa 'device_ip_in'
                        current_device_ip = data.get('device_ip_out', device_ip_in)                     

                        if data.get('device_ip_out'):
                            current_base_url = data.get('base_url_out', base_url_out)
                            id_user = data['id_user']
                        else:
                            current_base_url = base_url_in

                            if data.get('edit'):
                                id_user = data['id_user']
                            else:    
                                # Obtém o maior UserID e incrementa 1
                                url = f"http://{current_device_ip}/cgi-bin/recordFinder.cgi?action=doSeekFind&name=AccessControlCard"
                                
                                request_usuarios = Usuarios(url, username, password)
                                usuarios = request_usuarios.obter_usuarios()
                                maior_userid = request_usuarios.obter_maior_userid(usuarios)
                                novo_userid = int(maior_userid["UserID"]) + 1 if maior_userid else 1

                                id_user = novo_userid

                        print('IP RECEBIDO: ', current_device_ip)
                        print('URL RECEBIDA: ', current_base_url)

                        # Dados do usuário
                        user_data = {
                            "UserList": [
                                {
                                    "UserID": str(id_user),  # Usa o novo UserID
                                    "UserName": data['username'],
                                    "UserType": 0,
                                    "Authority": 2,
                                    "Password": data['password'],
                                    "Doors": [int(door) for door in data['doors']],  # Corrigido: converte cada elemento da lista para inteiro
                                    "TimeSections": [int(time_section) for time_section in data['time_sections']],  # Corrigido: converte cada elemento da lista para inteiro
                                    "ValidFrom": data['valid_from'].replace('T', ' '),  # Adiciona segundos 
                                    "ValidTo": data['valid_to'].replace('T', ' ')  # Adiciona segundos 
                                }
                            ]
                        }

                        # Criação da instância da API e envio dos dados do usuário
                        api = UserAPI(current_base_url, username, password)
                        api.send_user("insertMulti", user_data)

                        if True:
                        # if status_code == 200:
                            # Cadastra o CPF ou CardNo
                            card_data = {
                                "CardList": [
                                    {
                                        "UserID": str(id_user),
                                        "CardNo": data.get('cpf') or data.get('card_no'),  # Usa o CPF ou CardNo do usuário
                                        "CardType": "0",
                                        "CardStatus": "0"
                                    }
                                ]
                            }

                            # print('####### DADOS DO CPF: ',card_data)

                            card_url = f"http://{device_ip_out}/cgi-bin/AccessCard.cgi?action=insertMulti"
                            print('######### URL ATUALIZAR CPF: ',card_url)
                            card_api = UserAPI(card_url, username, password)
                            card_status_code, card_response_content = card_api.send_user("insertMulti", card_data)

                            print("Status Card", card_status_code, card_response_content)

                            # if True:
                            if card_status_code == 200:
                                # Recebe a foto da biometria em base64
                                foto_base64 = data.get('foto')
                                
                                if foto_base64:
                                    try:
                                        # Decodifica a imagem em base64
                                        foto_bytes = base64.b64decode(foto_base64)
                                        # Cria um objeto Imagem a partir dos bytes
                                        imagem = Image.open(io.BytesIO(foto_bytes))
                                        # Salva a imagem em um arquivo temporário                                        
                                        imagem.save(os.path.join(path_foto, 'foto.jpg'))
                                        image_path = os.path.join(path_foto, 'foto.jpg')
                                        biometric_registration = BiometricRegistration(current_device_ip, username, password)
                                        biometric_registration.register_face(str(id_user), image_path)

                                        # return jsonify(success=True, message='Usuário, CPF/CardNo e biometria cadastrados com sucesso!')
                                        print('Usuário, CPF/CardNo e biometria cadastrados com sucesso!')
                                    except Exception as e:
                                        # return jsonify(success=False, message=f"Erro ao decodificar a biometria")
                                        print("Erro ao decodificar a biometria")
                                else:
                                    # return jsonify(success=False, message='Foto da biometria não encontrada.')
                                    print('Foto da biometria não encontrada.')
                            else:
                                # return jsonify(success=False, message='Erro ao cadastrar CPF/CardNo.')
                                print('Erro ao cadastrar CPF/CardNo.')
                        else:
                            # return jsonify(success=False, message='Erro ao cadastrar usuário.')
                            print('Erro ao cadastrar usuário.')

                    # return jsonify(success=False, message='Requisição inválida.')
                    print('Requisição inválida.')
                
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
