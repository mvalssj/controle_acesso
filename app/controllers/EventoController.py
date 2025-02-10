import datetime # Importa o módulo datetime
import time
import traceback
from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from app.models import db, Evento, Unidade, Dashboard, Programacao, Equipamento, ProgramacaoCheck
from app.helpers.Intelbras import Usuarios, UserAPI
from sqlalchemy import func, and_, or_
from app.extensions import csrf  # Agora importa do extensions.py
import base64
import requests
import sys
import os
import re
import json
import subprocess
from datetime import date, datetime, timedelta
import app
from PIL import Image

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from config import unidade, catraca, siscomex, base_url_in, path_foto, username, password

class EventoController:
    def __init__(self):
        self.blueprint = Blueprint('evento', __name__)
        self.equipamento_controller = app.equipamento_controller # Armazena a instância

        # Rota para listar todos os eventos
        @self.blueprint.route('/eventos', methods=['GET', 'POST'])
        @csrf.exempt  # Usa a instância csrf para desabilitar CSRF nessa rota
        def eventos():
            # Obtém todos os eventos do banco de dados
            eventos = Evento.query.order_by(Evento.id.desc()).limit(300).all()
            unidades = Unidade.query.all()
            
            # Converte os eventos para um formato de dicionário
            eventos_data = [
                {
                    "id": evento.id,
                    "pessoa": evento.pessoa,
                    "cpf": evento.cpf,
                    "direcao": evento.direcao,
                    "retificacao": evento.retificacao,
                    "created_at": (evento.created_at - timedelta(hours=3)).strftime('%Y-%m-%d %H:%M:%S')  # Subtrai 3 horas e formata a data
                }
                for evento in eventos
            ]

            if request.method == 'POST':
                return jsonify(eventos_data)

            # Renderiza a página de eventos, passando a lista de eventos como contexto
            return render_template('eventos.html', eventos=eventos, unidades=unidades)
        
        # Rota para listar todos os eventos que só tiveram IN e ignorar código_erro = '16'
        @self.blueprint.route('/no_terminal', methods=['GET', 'POST'])
        @csrf.exempt  # Usa a instância csrf para desabilitar CSRF nessa rota
        def no_terminal():
            # Subconsulta para pegar o maior ID de eventos com direção 'OUT' para cada CPF
            subquery_last_out = (
                Evento.query
                .filter(Evento.direcao == 'OUT')
                .with_entities(Evento.cpf, func.max(Evento.id).label('last_out_id'))
                .group_by(Evento.cpf)
                .subquery()
            )
            
            # Calcula a data de dois dias atrás
            dois_dias_atras = datetime.now() - timedelta(days=2)
                # Subconsulta para pegar o último evento de IN para cada CPF, excluindo CPFs com OUT posterior,
            # eventos que tenham o código_erro = '16', eventos com CPF vazio e eventos com mais de dois dias.
            subquery_last_in = (
                Evento.query
                .outerjoin(subquery_last_out, Evento.cpf == subquery_last_out.c.cpf)
                .filter(
                    Evento.direcao == 'IN',  # Apenas eventos de IN
                    (subquery_last_out.c.last_out_id == None) | (Evento.id > subquery_last_out.c.last_out_id),  # Excluir CPFs com OUT posterior
                    Evento.codigo_erro != '16',  # Ignorar eventos com código_erro '16'
                    Evento.cpf != '',  # Ignorar eventos com CPF vazio
                    Evento.created_at >= dois_dias_atras # Considera apenas eventos dos últimos dois dias
                )
                .with_entities(Evento.cpf, func.max(Evento.id).label('last_in_id'))
                .group_by(Evento.cpf)
                .subquery()
            )
            
            # Consulta principal para pegar os eventos correspondentes ao último 'IN' de cada CPF
            eventos = (
                Evento.query
                .join(subquery_last_in, Evento.id == subquery_last_in.c.last_in_id)
                .distinct(Evento.cpf)  # Garantir que cada CPF seja listado apenas uma vez
                .filter(Evento.codigo_erro != '16')  # Garantir que a consulta final também ignora '16'
                .all()
            )
            
            # Converte os eventos para um formato de dicionário
            eventos_data = [
                {
                    "id": evento.id,
                    "pessoa": evento.pessoa,
                    "cpf": evento.cpf,
                    "created_at": (evento.created_at - timedelta(hours=3)).strftime('%Y-%m-%d %H:%M:%S')  # Subtrai 3 horas e formata a data
                }
                for evento in eventos
            ]           

            if request.method == 'POST':
                return jsonify(eventos_data)
            
            # Obtém todas as unidades
            unidades = Unidade.query.all()

            return render_template('no_terminal.html', eventos=eventos, unidades=unidades)

        # Rota para inserir um novo evento via Webhook
        @self.blueprint.route('/webhook/evento', methods=['POST'])
        @csrf.exempt  # Usa a instância csrf para desabilitar CSRF nessa rota
        def novo_evento():
            
            # Captura o ip das biometrias            
            ips_entrada, ips_saida = self.equipamento_controller.get_equipamento_id(unidade)
            # Itera sobre os IPs de entrada e saída
            for ip_entrada in ips_entrada:
                # print('##IP Entrada:', ip_entrada)
                device_ip_in = ip_entrada
                for ip_saida in ips_saida:
                    # print('##IP Saída:', ip_saida)
                    device_ip_out = ip_saida
                    # Captura o ip das biometrias

                    # Obtém os dados enviados como JSON
                    data = request.get_json()
                    # print('Json Recebido: ', data)
                    if not data:

                        return jsonify({"error": "Invalid or missing JSON data"}), 400
        
                    direcao = data.get('direcao')
                    codigo_erro = data.get('ErrorCode')
                    id_equipamento = data.get('UserID')
                    cpf = data.get('CardNo')
                    imagem_path = data.get('URL')
                    json_data = data

                    headers = {
                        'Content-Type': 'application/json',
                        'Postman-Token': '<calculated when request is sent>',
                        'User-Agent': 'PostmanRuntime/7.42.0',
                        'Accept': '*/*',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Connection': 'keep-alive'
                    }

                    if cpf !="":
                        # Define o corpo da requisição com o CPF
                        data_cpf = {'cpf': cpf}

                        # Faz a requisição POST para a rota /programacoes/cpf
                        try:
                            response_programacao = requests.post(
                                url_for('programacao.buscar_programacao_por_cpf', _external=True), 
                                headers=headers, 
                                json=data_cpf 
                            )
                        except Exception as e:
                            print(f"Erro ao fazer a requisição POST")

                        # Converte a resposta para JSON
                        try:
                            response_data = response_programacao.json()
                        except ValueError as e:
                            print(f"Erro ao converter resposta para JSON")
                            # Tratar o erro, talvez retornar um erro 500
                            # return

                        # Extrai as datas do JSON
                        datahora_fim = response_data.get("programacao", {}).get("datahora_fim")
                        datahora_inicio = response_data.get("programacao", {}).get("datahora_inicio")

                        if direcao =="IN":
                            datahora_fim = "2031-03-10T10:00:00"
                            datahora_inicio = "2024-03-10T10:00:00"
                        else:
                            # datahora_fim = datahora_fim + ":00"
                            # datahora_inicio = datahora_inicio + ":00"                            
                            datahora_fim = "2030-03-10T10:00:00"
                            datahora_inicio = "2024-03-10T10:00:00"

                    if (direcao == "IN" and cpf is not None and codigo_erro != "21" and codigo_erro != "16"):
                        
                        ## pega a foto do cadastro
                        url = f"http://{device_ip_in}/cgi-bin/AccessFace.cgi?action=list&UserIDList[0]={data.get('UserID')}"
                        digest_auth = requests.auth.HTTPDigestAuth(username, password)
                        rval = requests.get(url, auth=digest_auth, stream=True, timeout=20, verify=False)                
                        foto = rval.text           
                        # Extrair a string da resposta
                        response_text = foto
                        # Encontrar e extrair a string base64
                        photo_data_prefix = "FaceDataList[0].PhotoData[0]="
                        start_index = response_text.find(photo_data_prefix) + len(photo_data_prefix)
                        end_index = response_text.find("FaceDataList[0].UserID")
                        # Obter a parte relevante da string base64
                        photo_base64 = response_text[start_index:end_index].strip()
                        # Limpar a string base64 de caracteres de nova linha
                        clean_photo_base64 = photo_base64.replace("\r", "").replace("\n", "")
                        foto = clean_photo_base64
                        ## pega a foto do cadastro

                        direcao = data.get('direcao')
                        codigo_erro = data.get('ErrorCode')
                        id_equipamento = data.get('UserID')
                        id_evento = data.get('CreateTime')
                        pessoa = data.get('CardName')
                        cpf = data.get('CardNo')
                        imagem_path = data.get('URL')
                        id_user = data.get('UserID')
                        json_data = data
                        
                        # Define a direção com base no código de erro
                        if codigo_erro == "20":
                            direcao = None
    
                        # Verifica se o veiculo deverá ser pesado     
                        cavalo = response_data.get("programacao", {}).get("cavalo")
                        pos_fila = None
                        if cavalo is None or len(cavalo) < 7:
                            pesar = "N"
                        else:
                            pesar = "Y"
                        # Consulta para armazenar o resultado
                            fila = Evento.query.filter(Evento.pos_fila != '').order_by(Evento.pos_fila.desc()).first()  # Armazena o último pos_fila
                            fila = 0 if fila is None else fila  # Se fila for None, pos_fila será 0
                            print('############# Fila: ',fila.pos_fila)
                            pos_fila = 0
                            pos_fila = fila.pos_fila + 1
                        # Verifica se o veiculo deverá ser pesado     
                        
                        # Cria um novo objeto Evento
                        novo_evento = Evento(direcao=direcao, codigo_erro=codigo_erro, id_equipamento=id_equipamento, id_evento=id_evento, imagem_path=imagem_path, json=json_data, cpf=cpf, pessoa=pessoa, pos_fila=pos_fila, pesar=pesar)

                        # Verifica se já existe um evento com o mesmo id_evento
                        evento_existente = Evento.query.filter_by(id_evento=id_evento).first()
                        if evento_existente:
                            print("Evento já adicionado")
                            # return jsonify({"status": "Evento Duplicado!"})
                        else:
                            # Adiciona o novo evento ao banco de dados
                            try:
                                db.session.add(novo_evento)
                                db.session.commit() 
                            except Exception as e:
                                print(f"Erro ao inserir evento")
                                # return jsonify({"status": "Erro ao inserir evento!"})               

                            # --- Início da integração com Siscomex ---
                            if novo_evento.id and codigo_erro != "20":  # Verifica se o evento foi inserido com sucesso
                                
                                ### Paga a placa Frontal ###
                                cavalo = response_data.get("programacao", {}).get("cavalo")
                                print('Placa Cavalo: ',cavalo)    
                                if cavalo != '':
                                    print('##### Pegando Placa #####')
                                    subprocess.call(["python", "app\\services\\lpr\\lpr.py"])
                                ### Paga a placa Frontal ###

                                # Envio siscomex
                                siscomex_in = {
                                    "tipoOperacao": "I",
                                    "cpf": cpf,
                                    "direcao": "E",
                                    "identificacao": "2",
                                    "nome": pessoa,
                                    "catraca": catraca
                                }

                                # protocolo = enviar_siscomex(siscomex_in)
                                # print("Protocolo: ",protocolo)
                                # # Grava protocolo na tupla
                                # novo_evento.protocolo = protocolo
                                # db.session.commit()
                            # --- Fim da integração com Siscomex ---

                            json_saida = {
                                "username": pessoa,
                                "password": "142114",
                                "doors": [0],
                                "time_sections": [2],
                                "valid_from": "2024-03-10T10:00:00",
                                "valid_to": "2032-03-10T10:00:00",
                                "foto": foto,
                                "cpf": cpf,
                                "id_user": id_user,
                                "device_ip_out": device_ip_out
                            }     
                            # print('########## Json saida: ',json_saida)           

                            response_saida = requests.post(url_for('programacao.api_cadastrar', _external=True), headers=headers, json=json_saida)

                            json_antipassback_in = {
                                "username": pessoa,
                                "password": "142114",
                                "doors": [0],
                                "time_sections": [2],
                                "valid_from": datahora_inicio,
                                "valid_to": datahora_fim,
                                "id_user": id_user,
                                "edit": 1
                            }
                    
                            if codigo_erro == "20":
                                direcao = None
                                # Atualiza o campo 'gracacao_equipamento' para 'N'
                                novo_evento.gravacao_equipamento = 'N'
                                db.session.commit()
                            else:
                                response_antipassback = requests.post(url_for('programacao.api_cadastrar', _external=True), headers=headers, json=json_antipassback_in)
                                # Atualiza o campo 'gracacao_equipamento' para 'Y'
                                novo_evento.gravacao_equipamento = 'Y'
                                db.session.commit()

                        # Valida se os campos necessários foram recebidos
                        if not id_equipamento or not imagem_path or not json_data:
                            print('Campos necessários não recebidos')

                        # Verifica se o campo CPF está vazio e se não está programado
                        if not cpf:
                            
                            print('Pessoa não identificada ou sem programação.')
                    
                    try:
                    
                        # Remove a pessoa do equipamento
                        if direcao == "OUT" and cpf is not None:

                            direcao = data.get('direcao')
                            codigo_erro = data.get('ErrorCode')
                            id_equipamento = data.get('UserID')
                            id_evento = data.get('CreateTime')
                            pessoa = data.get('CardName')
                            cpf = data.get('CardNo')
                            imagem_path = data.get('URL')
                            id_user = data.get('UserID')
                            json_data = data
                             
                            # Verifica se o veiculo deverá ser pesado     
                            cavalo = response_data.get("programacao", {}).get("cavalo")
                            pos_fila = None
                            if cavalo is None or len(cavalo) < 7:
                                pesar = "N"
                            else:
                                pesar = "Y"
                                fila = Evento.query.filter(Evento.pos_fila != '').order_by(Evento.pos_fila.desc()).first()  # Armazena o último pos_fila
                                fila = 0 if fila is None else fila  # Se fila for None, pos_fila será 0
                                print('############# Fila: ',fila.pos_fila)
                                pos_fila = 0
                                pos_fila = fila.pos_fila + 1
                            # Verifica se o veiculo deverá ser pesado    

                            # Cria um novo objeto Evento
                            novo_evento = Evento(direcao=direcao, codigo_erro=codigo_erro, id_equipamento=id_equipamento, id_evento=id_evento, imagem_path=imagem_path, json=json_data, cpf=cpf, pessoa=pessoa, pos_fila=pos_fila, pesar=pesar)

                            # Verifica se já existe um evento com o mesmo id_evento
                            evento_existente = Evento.query.filter_by(id_evento=id_evento).first()
                            if evento_existente:
                                print("Evento já adicionado")
                                # return jsonify({"status": "Evento Duplicado!"})
                            else:
                                # Adiciona o novo evento ao banco de dados
                                try:
                                    db.session.add(novo_evento)
                                    db.session.commit() 
                                except Exception as e:
                                    print(f"Erro ao inserir evento no banco!")

                            # --- Início da integração com Siscomex ---
                            if novo_evento.id and codigo_erro != "20":  # Verifica se o evento foi inserido com sucesso
                                # Envio siscomex
                                siscomex_out = {
                                    "tipoOperacao": "I",
                                    "cpf": cpf,
                                    "direcao": "S",
                                    "identificacao": "2",
                                    "nome": pessoa,
                                    "catraca": catraca
                                }

                                # protocolo = enviar_siscomex(siscomex_out)
                                # # Grava protocolo na tupla
                                # novo_evento.protocolo = protocolo
                                # db.session.commit()
                            # --- Fim da integração com Siscomex ---

                            json_data = {
                                "UserList": [
                                    {
                                        "UserID": id_user,
                                        "UserName": pessoa,
                                        "UserType": 0,
                                        "Authority": 0,
                                        "Password": "142114",
                                        "Doors": [0],
                                        "TimeSections": [2],
                                        "ValidFrom": "2024-03-10T10:00:00", 
                                        "ValidTo": "2033-03-10T10:00:00"
                                    }
                                ]
                            }

                            url = f"http://{device_ip_out}/cgi-bin/AccessUser.cgi?action=insertMulti"

                            def send_user(url, json_data, username, password):
                                try:
                                    # Realiza a requisição HTTP POST com autenticação digest
                                    response = requests.post(url, auth=requests.auth.HTTPDigestAuth(username, password), json=json_data)
                                    response.raise_for_status()  # Levanta uma exceção para códigos de status HTTP de erro
                                    return response.status_code, response.content
                                except requests.exceptions.RequestException as e:
                                    print(f"Erro ao fazer a requisição POST para {url}: {e}")
                                    traceback.print_exc()  # Imprime a stack trace completa do erro
                                    return None, None
                                 
                            status_code, response_content = send_user(url, json_data, username, password)
                                                                        
                            url = f"http://{device_ip_in}/cgi-bin/AccessUser.cgi?action=insertMulti"
                            
                            json_data = {
                                "UserList": [
                                    {
                                        "UserID": id_user,
                                        "UserName": pessoa,
                                        "UserType": 0,
                                        "Authority": 0,
                                        "Password": "142114",
                                        "Doors": [0],
                                        "TimeSections": [2],
                                        "ValidFrom": datahora_inicio.replace('T', ' '),
                                        "ValidTo": datahora_fim.replace('T', ' ')
                                    }
                                ]
                            }
                            
                            def send_user(url, json_data, username, password):
                                try:
                                    # Realiza a requisição HTTP POST com autenticação digest
                                    response = requests.post(url, auth=requests.auth.HTTPDigestAuth(username, password), json=json_data)
                                    response.raise_for_status()  # Levanta uma exceção para códigos de status HTTP de erro
                                    return response.status_code, response.content
                                except requests.exceptions.RequestException as e:
                                    print(f"Erro ao fazer a requisição POST para {url}: {e}")
                                    traceback.print_exc()  # Imprime a stack trace completa do erro
                                    return None, None
                                                
                            if codigo_erro == "20":
                                direcao = None
                                # Atualiza o campo 'gracacao_equipamento' para 'N'
                                novo_evento.gravacao_equipamento = 'N'
                                db.session.commit()

                                novo_evento.direcao = direcao
                                db.session.commit()

                            else:
                                status_code, response_content = send_user(url, json_data, username, password)
                                # Atualiza o campo 'gracacao_equipamento' para 'Y'
                                novo_evento.gravacao_equipamento = 'Y'
                                db.session.commit()

                        # print('Evento enviado com sucesso!')          
                    except Exception as e:
                        # print(f"Erro ao inserir evento ####Corrigir####: {e}")
                        print('Dentro do Erro: ###### IP Entrada: ######', device_ip_in)
                        print('Dentro do Erro: ###### IP Saída: ######', device_ip_out)
                        traceback.print_exc()  # Imprime a stack trace completa do erro

            return jsonify({"status": "success", "message": "Evento inserido com sucesso"}), 200 
                        
        # Rota para adequar um evento em caso de não conformidade   
        @self.blueprint.route('/adequar_evento', methods=['POST'])
        @csrf.exempt  # Usa a instância csrf para desabilitar CSRF nessa rota
        def adequar_evento():

            # Captura o ip das biometrias
            ips_entrada, ips_saida = self.equipamento_controller.get_equipamento_id(unidade)
            for ip_entrada in ips_entrada:
                for ip_saida in ips_saida:
                    print('IP Entrada:', ip_entrada)
                    print('IP Saída:', ip_saida)
                    device_ip_in = ip_entrada
                    device_ip_out = ip_saida                        
                    # Captura o ip das biometrias

                    # Obtém os dados enviados como JSON
                    data = request.get_json()
                    # print('Json Recebido: ', data)

                    headers = {
                        'Content-Type': 'application/json',
                        'Postman-Token': '<calculated when request is sent>',
                        'User-Agent': 'PostmanRuntime/7.42.0',
                        'Accept': '*/*',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Connection': 'keep-alive'
                    }

                    direcao = data['direcao']
                    cpf = data['CardNo']
                    nome = data['CardName']  # Mantém o nome recebido do JSON
                    id_evento = data['IdEvento']

                    print('###### direção:',direcao)

                    if direcao != "IN":
                        current_device_ip = device_ip_in
                        direcao = "OUT"
                    else:        
                        current_device_ip = device_ip_out   
                        
                    if not data:
                        print("Invalid or missing JSON data")
                    else:
                        # Pegar ID da pessoa no equipamento
                        url_equipamento = f"http://{current_device_ip}/cgi-bin/AccessCard.cgi?action=list&CardNoList[0]={cpf}"

                        digest_auth = requests.auth.HTTPDigestAuth(username, password)
                        rval = requests.get(url_equipamento, auth=digest_auth, stream=True, timeout=20, verify=False)
                        # Pegar ID da pessoa no equipamento          
                        try:
                            # Use regex para encontrar o UserID na resposta de texto
                            match = re.search(r'Cards\[0\]\.UserID=(\d+)', rval.text)
                            if match:
                                id_user = match.group(1)  # Pegue o primeiro grupo encontrado (número do UserID)
                                print(f"UserID: {id_user}")
                            else:
                                print("UserID não encontrado na resposta")
                                # return jsonify({"error": "UserID não encontrado"}), 500

                        except Exception as e:
                            print(f"Erro ao extrair UserID: {e}")
                            # Tratar o erro adequadamente, talvez retornar um erro 500
                            # return jsonify({"error": "Erro ao extrair UserID"}), 500
                        # Extrair o valor de UserID do JSON retornado   

                        url_foto = f"http://{current_device_ip}/cgi-bin/AccessFace.cgi?action=list&UserIDList[0]={id_user}"

                        rval = requests.get(url_foto, auth=digest_auth, stream=True, timeout=20, verify=False)
                        foto = rval.text
                        
                        # Extrair a string da resposta
                        response_text = foto
                        
                        # Encontrar e extrair a string base64
                        photo_data_prefix = "FaceDataList[0].PhotoData[0]="
                        start_index = response_text.find(photo_data_prefix) + len(photo_data_prefix)
                        end_index = response_text.find("FaceDataList[0].UserID")

                        # Obter a parte relevante da string base64
                        photo_base64 = response_text[start_index:end_index].strip()

                        # Limpar a string base64 de caracteres de nova linha
                        clean_photo_base64 = photo_base64.replace("\r", "").replace("\n", "")
                        foto = clean_photo_base64

                        if cpf !="":
                            # Define o corpo da requisição com o CPF
                            data_cpf = {'cpf': cpf}
                            # Faz a requisição POST para a rota /programacoes/cpf
                            try:
                                response_programacao = requests.post(
                                    url_for('programacao.buscar_programacao_por_cpf', _external=True), 
                                    headers=headers, 
                                    json=data_cpf 
                                )
                            except Exception as e:
                                print(f"Erro ao fazer a requisição POST")

                            # Converte a resposta para JSON
                            try:
                                response_data = response_programacao.json()
                            except ValueError as e:
                                print(f"Erro ao converter resposta para JSON")

                        # Extrai as datas do JSON
                        datahora_fim = response_data.get("programacao", {}).get("datahora_fim")
                        datahora_inicio = response_data.get("programacao", {}).get("datahora_inicio")

                        datahora_fim = datahora_fim + ":00"
                        datahora_inicio = datahora_inicio + ":00"

                    json_saida = {
                        "username": nome,  # Use o nome que foi obtido
                        "password": "142114",
                        "doors": [0],
                        "time_sections": [2],
                        "valid_from": datahora_inicio,
                        "valid_to": datahora_fim,
                        "foto": foto,
                        "cpf": cpf,
                        "id_user": id_user,
                        "device_ip_out": device_ip_out
                    }

                    json_antipassback = {
                        "username": nome,  # Use o nome que foi obtido
                        "password": "142114",
                        "doors": [0],
                        "time_sections": [2],
                        "valid_from": datahora_inicio,
                        "valid_to": datahora_fim,
                        "foto": foto,
                        "cpf": cpf,
                        "id_user": id_user,
                        "edit": 1
                    }

                    if (direcao == "OUT" and cpf is not None):
                        response_saida = requests.post(url_for('programacao.api_cadastrar', _external=True), headers=headers, json=json_saida)

                        response_antipassback = requests.post(url_for('programacao.api_cadastrar', _external=True), headers=headers, json=json_antipassback)

                        # Encontre o evento que você deseja atualizar
                        evento = Evento.query.filter_by(id=id_evento).first()
        
                        # Verifique se o evento foi encontrado
                        if evento:
                            # Atualize os atributos do evento
                            evento.direcao = "IN"
                            evento.retificacao = "Y"
                            # Salve as alterações no banco de dados
                            db.session.commit()

                        else:
                            # Retorne uma resposta de erro se o evento não foi encontrado
                            print("Evento não encontrado")
                            # return jsonify({"status": "error", "message": "Evento não encontrado"}), 404
                    
                    else: # Remove a pessoa do equipamento
                        if direcao == "IN" and cpf is not None:
                            print('Ativando Antipassback de saida...')   

                            json_data = {
                                "UserList": [
                                    {
                                        "UserID": id_user,
                                        "UserName": nome,
                                        "UserType": 0,
                                        "Authority": 0,
                                        "Password": "142114",
                                        "Doors": [0],
                                        "TimeSections": [2],
                                        "ValidFrom": "2024-03-10T10:00:00",
                                        "ValidTo": "2033-03-10T10:00:00"
                                    }
                                ]
                            }

                            url = f"http://{device_ip_out}/cgi-bin/AccessUser.cgi?action=insertMulti"

                            def send_user(url, json_data, username, password):
                                # Realiza a requisição HTTP POST com autenticação digest
                                response = requests.post(url, auth=requests.auth.HTTPDigestAuth(username, password), json=json_data)
                            
                            status_code, response_content = send_user(url, json_data, username, password)
                            
                            print("Status Code:", status_code)
                            print("Response Content:", response_content)

                            response_antipassback_out = requests.post(url_for('programacao.api_cadastrar', _external=True), headers=headers, json=json_antipassback)

                            # Encontre o evento que você deseja atualizar
                            evento = Evento.query.filter_by(id=id_evento).first()

                            # Verifique se o evento foi encontrado
                            if evento:
                                # Atualize os atributos do evento
                                evento.direcao = "OUT"
                                evento.retificacao = "Y"

                                # Salve as alterações no banco de dados
                                db.session.commit()

                                # Retorne uma resposta de sucesso
                                print("Evento atualizado com sucesso")
                            else:
                                # Retorne uma resposta de erro se o evento não foi encontrado
                                print("Esso ao atualizar evento")
 
        # Rota para atualizar um evento
        @self.blueprint.route('/eventos/<int:id>/editar', methods=['GET', 'POST'])
        def editar_evento(id):
            # Obtém o evento a ser editado
            evento = Evento.query.get_or_404(id)

            # Se o método for POST, atualiza o evento
            if request.method == 'POST':
                # Obtém os dados do formulário
                id_equipamento = request.form.get('id_equipamento')
                imagem_path = request.form.get('imagem_path')
                json = request.form.get('json')

                # Atualiza os dados do evento
                evento.id_equipamento = id_equipamento
                evento.imagem_path = imagem_path
                evento.json = json

                # Salva as alterações no banco de dados
                db.session.commit()
                
                # Redireciona para a página de eventos
                return redirect(url_for('evento.eventos'))

            # Se o método for GET, renderiza a página de edição
            return render_template('editar_evento.html', evento=evento)

        # Rota para apagar um evento
        @self.blueprint.route('/eventos/<int:id>/apagar', methods=['POST'])
        def apagar_evento(id):
            # Obtém o evento a ser apagado
            evento = Evento.query.get_or_404(id)

            # Remove o evento do banco de dados
            db.session.delete(evento)
            db.session.commit()

            # Redireciona para a página de eventos após a exclusão
            return redirect(url_for('evento.eventos'))

        # Rota para obter o primeiro da fila da balanca
        @self.blueprint.route('/fila_balanca')
        def fila_balanca():
            # Captura o ip das biometrias
            ips_entrada, ips_saida = self.equipamento_controller.get_equipamento_id(unidade)
            
            direcao = request.args.get('direcao')  # Obtém a direção da requisição
            verificar_direcao(direcao)

            print('DIRECAO: ##########',direcao)
            # Carrega as imagens base64
            with open("app\\services\\lpr\\images\\live.jpg", "rb") as image_file:
                placa_frontal_entrada_base64 = base64.b64encode(image_file.read()).decode('utf-8')

            with open("app\\services\\lpr\\images\\placa_frontal.jpg", "rb") as image_file:
                placa_frontal_balanca_base64 = base64.b64encode(image_file.read()).decode('utf-8')

            with open("app\\services\\lpr\\images\\placa_traseira.jpg", "rb") as image_file:
                placa_traseira_balanca_base64 = base64.b64encode(image_file.read()).decode('utf-8')

            with open("app\\services\\lpr\\images\\truck.jpg", "rb") as image_file:
                container_superior_base64 = base64.b64encode(image_file.read()).decode('utf-8')

            with open("app\\services\\lpr\\images\\pedestre.jpg", "rb") as image_file:
                pedestre_base64 = base64.b64encode(image_file.read()).decode('utf-8')

            # Itera sobre os IPs de entrada e saída
            if ips_entrada or ips_saida:
                for ip_entrada in ips_entrada:
                    for ip_saida in ips_saida:
                        print('IP Entrada:', ip_entrada)
                        print('IP Saída:', ip_saida)
                        device_ip_in = ip_entrada
                        device_ip_out = ip_saida

                        # Consulta principal para encontrar eventos de entrada e saída com pesar='Y' sem evento de saída posterior
                        def obter_eventos_por_direcao(direcao = 0):
                            # Função para obter eventos com base na direção
                            if direcao == "1":  # Direção IN
                                eventos = (
                                    Evento.query
                                    .filter(Evento.direcao == 'IN', Evento.pesar == 'Y', Evento.pos_fila != '')
                                    .order_by(Evento.pos_fila.desc())
                                    .all()
                                )
                            elif direcao == "2":  # Direção OUT
                                eventos = (
                                    Evento.query
                                    .filter(Evento.direcao == 'OUT', Evento.pesar == 'Y', Evento.pos_fila != '')
                                    .order_by(Evento.pos_fila.desc())
                                    .all()
                                )
                            else:  # Ambas as direções
                                eventos = (
                                    Evento.query
                                    .filter(Evento.pesar == 'Y', Evento.pos_fila != '')
                                    .order_by(Evento.pos_fila.desc())
                                    .all()
                                )
                            return eventos
                        
                        eventos = obter_eventos_por_direcao(direcao)
                        
                        # Combina as listas, com os eventos 'OUT' no início
                        eventos_pesar = eventos

                        # Define ultimo_evento como o primeiro da lista eventos_pesar
                        ultimo_evento = eventos_pesar[0] if eventos_pesar else None

                        if not ultimo_evento:
                            return jsonify({'message': 'Nenhum motorista na fila da balança.'}), 200

                        # Define a mensagem de acordo com o código de erro
                        if ultimo_evento.codigo_erro == "21":
                            mensagem = "Bloqueado por Antipassback"
                        elif ultimo_evento.codigo_erro == "0":
                            mensagem = "Liberado"
                        else:
                            mensagem = ""

                        print('###Eventos:',eventos)
                        if ultimo_evento.direcao == "OUT":
                            current_device_ip = device_ip_out
                            print('####### IP de Saida: ',current_device_ip)
                        else:
                            current_device_ip = device_ip_in
                            print('####### IP de Entrada: ',current_device_ip)

                        url_imagem = f"http://{current_device_ip}/cgi-bin/FileManager.cgi?action=downloadFile&fileName={ultimo_evento.imagem_path}"

                        auth = requests.auth.HTTPDigestAuth(username, password)
                        response = requests.get(url_imagem, auth=auth)

                        if response.status_code == 200:
                            imagem_base64 = base64.b64encode(response.content).decode('utf-8')

                            return jsonify({
                                'cpf': ultimo_evento.cpf,
                                'pessoa': ultimo_evento.pessoa,
                                'imagem_path': ultimo_evento.imagem_path,
                                'imagem_base64': imagem_base64,
                                'direcao': ultimo_evento.direcao,
                                'codigo_erro': ultimo_evento.codigo_erro,
                                'mensagem': mensagem,
                                'placa_frontal': placa_frontal_entrada_base64,
                                'placa_frontal_balanca': placa_frontal_balanca_base64,
                                'placa_traseira_balanca': placa_traseira_balanca_base64,
                                'container_superior': container_superior_base64,
                                'pedestre': pedestre_base64
                            })

                        else:

                            return jsonify({
                                'cpf': ultimo_evento.cpf,
                                'pessoa': ultimo_evento.pessoa,
                                'imagem_path': ultimo_evento.imagem_path,
                                'codigo_erro': ultimo_evento.codigo_erro,
                                'mensagem': mensagem,
                                'erro': f"Falha ao obter a imagem. Status code: {response.status_code}"
                            })
            else:
                return jsonify({
                    # 'cpf': "03457462526",
                    # 'imagem_path': ultimo_evento.imagem_path,
                    # 'imagem_base64': imagem_base64,
                    # 'pessoa': "EMIVAL SANTOS SILVA",
                    'direcao': "IN",
                    'codigo_erro': "0",
                    'mensagem': "Liberado",
                    'placa_frontal': placa_frontal_entrada_base64,
                    'placa_frontal_balanca': placa_frontal_balanca_base64,
                    'placa_traseira_balanca': placa_traseira_balanca_base64,
                    'container_superior': container_superior_base64,
                    'pedestre': pedestre_base64
                })
            
        # Rota para obter o último CPF inserido
        @self.blueprint.route('/ultimo_cpf')
        def ultimo_cpf():

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

                    # Obtém o último evento inserido
                    ultimo_evento = Evento.query.order_by(Evento.id.desc()).first()
                    
                    # Define a mensagem de acordo com o código de erro
                    if ultimo_evento.codigo_erro == "20" and ultimo_evento.retificacao == "N":
                        mensagem = "Bloqueado por Antipassback"
                    else:
                        mensagem = "Liberado"

                    # Define a variável `current_device_ip` com base na direção do evento
                    if ultimo_evento.direcao == "OUT":
                        current_device_ip = device_ip_out
                    elif ultimo_evento.direcao == "IN":
                        current_device_ip = device_ip_in                        
                    else:
                        current_device_ip = device_ip_in

                    # Montar a URL com base no imagem_path usando `current_device_ip`
                    url_imagem = f"http://{current_device_ip}/cgi-bin/FileManager.cgi?action=downloadFile&fileName={ultimo_evento.imagem_path}"

                    # Carrega a imagem da placa frontal da entrada
                    with open("app\\services\\lpr\\images\\live.jpg", "rb") as image_file:
                        placa_frontal_entrada_base64 = base64.b64encode(image_file.read()).decode('utf-8')

                    # Carrega a imagem da placa frontal da balanca
                    with open("app\\services\\lpr\\images\\placa_frontal.jpg", "rb") as image_file:
                        placa_frontal_balanca_base64 = base64.b64encode(image_file.read()).decode('utf-8')

                    # Carrega a imagem da placa frontal da traseira
                    with open("app\\services\\lpr\\images\\placa_traseira.jpg", "rb") as image_file:
                        placa_traseira_balanca_base64 = base64.b64encode(image_file.read()).decode('utf-8')

                    # Carrega a imagem do truck                    
                    with open("app\\services\\lpr\\images\\truck.jpg", "rb") as image_file:
                        container_superior_base64 = base64.b64encode(image_file.read()).decode('utf-8')

                    # Carrega a imagem padrão de pedestre
                    with open("app\\services\\lpr\\images\\pedestre.jpg", "rb") as image_file:
                        pedestre_base64 = base64.b64encode(image_file.read()).decode('utf-8')

                    # Autenticação (igual ao exemplo do arquivo foto.py)
                    auth = requests.auth.HTTPDigestAuth(username, password)

                    # Baixar a imagem
                    response = requests.get(url_imagem, auth=auth)

                    if response.status_code == 200:
                        imagem_base64 = base64.b64encode(response.content).decode('utf-8')
                    else: 
                        current_device_ip = device_ip_out
                        
                        url_imagem = f"http://{current_device_ip}/cgi-bin/FileManager.cgi?action=downloadFile&fileName={ultimo_evento.imagem_path}"

                        response = requests.get(url_imagem, auth=auth)
                        # Codificar o conteúdo da imagem em base64 para enviar no JSON
                        imagem_base64 = base64.b64encode(response.content).decode('utf-8')

                    if response.status_code == 200:
                        # Retorna o CPF, imagem_path, imagem_base64, código de erro e mensagem como JSON
                        # print(imagem_base64)

                        return jsonify({
                            'id': ultimo_evento.id,
                            'cpf': ultimo_evento.cpf,
                            'imagem_path': ultimo_evento.imagem_path,
                            'imagem_base64': imagem_base64,
                            'codigo_erro': ultimo_evento.codigo_erro,
                            'mensagem': mensagem,
                            'placa_frontal': placa_frontal_entrada_base64,  # Adiciona a imagem da placa frontal entrada
                            'placa_frontal_balanca': placa_frontal_balanca_base64,  # Adiciona a imagem da placa frontal balança
                            'placa_traseira_balanca': placa_traseira_balanca_base64,  # Adiciona a imagem da placa frontal balança
                            'container_superior': container_superior_base64,  # Adiciona a imagem da placa frontal balança
                            'pedestre': pedestre_base64  # Adiciona a imagem 
                        })
                                        
                    else:
                        # Se a imagem não foi obtida, retornar uma mensagem de erro
                        return jsonify({
                            'id': ultimo_evento.id,
                            'cpf': ultimo_evento.cpf,
                            'imagem_path': ultimo_evento.imagem_path,
                            'codigo_erro': ultimo_evento.codigo_erro,
                            'mensagem': mensagem,
                            'erro': f"Falha ao obter a imagem. Status code: {response.status_code}"
                        })   

        # Rota para obter a fila de motoristas que ainda não pesaram
        @self.blueprint.route('/fila_motoristas_pesar')
        def fila_motoristas_pesar():
            
            direcao = request.args.get('direcao')  # Obtém a direção da requisição

            # Consulta principal para encontrar eventos de entrada e saída com pesar='Y' sem evento de saída posterior
            def obter_eventos_por_direcao(direcao = 0):
                # Função para obter eventos com base na direção
                if direcao == "1":  # Direção IN
                    eventos = (
                        Evento.query
                        .filter(Evento.direcao == 'IN', Evento.pesar == 'Y', Evento.pos_fila != '')
                        .order_by(Evento.pos_fila.desc())
                        .all()
                    )
                elif direcao == "2":  # Direção OUT
                    eventos = (
                        Evento.query
                        .filter(Evento.direcao == 'OUT', Evento.pesar == 'Y', Evento.pos_fila != '')
                        .order_by(Evento.pos_fila.desc())
                        .all()
                    )
                else:  # Ambas as direções
                    eventos = (
                        Evento.query
                        .filter(Evento.pesar == 'Y', Evento.pos_fila != '')
                        .order_by(Evento.pos_fila.desc())
                        .all()
                    )
                return eventos
            
            eventos = obter_eventos_por_direcao(direcao)

            # Combina as listas, com os eventos 'OUT' no início
            eventos_pesar = eventos

            # Formata os dados para a resposta JSON
            eventos_pesar_data = [
                {
                    "id": evento.id,
                    "pessoa": evento.pessoa,
                    "cpf": evento.cpf,
                    "direcao": evento.direcao,
                    "created_at": evento.created_at.strftime('%Y-%m-%d %H:%M:%S')
                }
                for evento in eventos_pesar
            ]

            return jsonify(eventos_pesar_data)

        # Envia os acessos para a API recintos
        def enviar_siscomex(siscomex_json):

            print("Entrou no Siscomex")

            url = siscomex 
            headers = {
                'Content-Type': 'application/json'
            }
            
            try:
                response = requests.post(url, json=siscomex_json, headers=headers)
                print("Status Code:", response.status_code)
                
                # Exibe o conteúdo completo da resposta
                response_text = response.text
                print("Response Content:", response_text)

                # Localiza o início do JSON dentro da resposta
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1

                if json_start != -1 and json_end != -1:
                    # Extrai apenas a parte que parece ser o JSON válido
                    json_part = response_text[json_start:json_end]
                    print("Parte JSON extraída:", json_part)
                    try:
                        # Faz o parse do JSON
                        response_json = json.loads(json_part)
                        print("Acesso enviado com sucesso!", response_json)
                        protocolo = response_json.get("protocolo")
                        print('Protocolo: ', protocolo)  # Exibe o protocolo aqui

                        if response.status_code == 200:                            
                            return protocolo  # Retorna o protocolo aqui
                        else:
                            print('!!!Não retornou 200!!!')
                            return response_json 

                    except ValueError as e:
                        print(f"Erro ao decodificar JSON")
                        # Exibe o conteúdo bruto da resposta para análise
                        print("Resposta bruta que causou o erro:", response_text)
                
                else:
                    print("Nenhum JSON válido encontrado na resposta.")
                
                response.raise_for_status()  # Levanta um erro para códigos de status HTTP 4xx/5xx

            except requests.exceptions.HTTPError as http_err:
                print(f"Erro HTTP: {http_err}")
            except Exception as err:
                print(f"Erro ao enviar a requisição Siscomex")
                return None

        # Atualiza com a placa do lpr ou manual   
        def capturar_placa(self, cpf):

            print('#### Entrou no Captura Placa ####')
            try:
                # Encontra o último evento com o CPF fornecido
                ultimo_evento = Evento.query.filter_by(cpf=cpf).order_by(Evento.id.desc()).first()

                if not ultimo_evento:
                    print(f"Nenhum evento encontrado para o CPF {cpf}")
                    return

                # Lê a placa do arquivo
                try:
                    with open("app\\services\\lpr\\placa_frontal.txt", "r") as f:
                        placa_frontal = f.read().strip()
                except FileNotFoundError:
                    print("Arquivo placa_frontal.txt não encontrado!")
                    return
                except Exception as e:
                    print(f"Erro ao ler a placa: {e}")
                    return

                # Atualiza o evento
                ultimo_evento.placa_1 = placa_frontal
                ultimo_evento.lpr = "Y"
                db.session.commit()

                print(f"Evento atualizado com sucesso para o CPF {cpf}. Placa: {placa_frontal}")

            except Exception as e:
                print(f"Erro ao capturar e atualizar a placa: {e}")

        @self.blueprint.route('/checa_placas', methods=['GET', 'POST'])
        def checa_placas():
            tipo = request.args.get('tipo')  # Obtém o parâmetro 'tipo' da requisição
            headers = {
                'Content-Type': 'application/json',
                'Postman-Token': '<calculated when request is sent>',
                'User-Agent': 'PostmanRuntime/7.42.0',
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive'
            }

            try:
                response_data = app.serve_placa_balanca().json

                placa_frontal = response_data.get("placa_frontal", "N/A")
                placa_traseira = response_data.get("placa_traseira", "N/A")

                # Função para obter eventos com base na direção
                def obter_eventos_por_direcao():
                    eventos_resultados = {
                        "entrada": Evento.query.filter(Evento.direcao == 'IN', Evento.pesar == 'Y', Evento.pos_fila != '').order_by(Evento.pos_fila.desc()).all(),
                        "saida": Evento.query.filter(Evento.direcao == 'OUT', Evento.pesar == 'Y', Evento.pos_fila != '').order_by(Evento.pos_fila.desc()).all()
                    }
                    return eventos_resultados

                eventos = obter_eventos_por_direcao()  # Chama a função

                resultados = []  # Para armazenar os resultados de entrada e saída

                # Iteração para as listas de entrada e saída
                for direcao_nome, eventos_lista in eventos.items():
                    for ultimo_evento in eventos_lista:
                        pessoa = ultimo_evento.pessoa
                        evento_id = ultimo_evento.id
                        cpf_primeiro_da_fila = ultimo_evento.cpf

                        if not cpf_primeiro_da_fila:
                            continue  # Pula para o próximo evento se o CPF não estiver disponível

                        try:
                            response_programacao = requests.post(
                                url_for('programacao.buscar_programacao_por_cpf', _external=True),
                                headers=headers,
                                json={'cpf': cpf_primeiro_da_fila}
                            )
                            response_programacao.raise_for_status()
                            response_data = response_programacao.json()

                            programacao = response_data.get("programacao", {})
                            if not programacao:
                                continue  # Pula para o próximo evento se não houver programação

                            carreta_programacao = programacao.get("carreta")
                            cavalo_programacao = programacao.get("cavalo")
                            pessoa_programacao = programacao.get("pessoa")
                            cpf_programacao = programacao.get("cpf")

                            status_pessoa = "ok" if cpf_programacao == cpf_primeiro_da_fila else "nok"
                            status_frontal = "ok" if cavalo_programacao == placa_frontal else "nok"
                            status_traseira = "ok" if carreta_programacao == placa_traseira else "nok"
                            status_geral = "ok" if status_frontal == "ok" and status_traseira == "ok" and status_pessoa == "ok" else "nok"

                            # Se tiver Ok tudo ok
                            if status_geral == "ok":
                                try:
                                    with open('app\\services\\lpr\\placa_frontal_balanca.txt', 'w') as f:
                                        f.write("N/A")
                                    with open('app\\services\\lpr\\placa_traseira_balanca.txt', 'w') as f:
                                        f.write("N/A")

                                    imagem_branca = Image.new("RGB", (1280, 720), "white")
                                    imagem_branca.save('app\\services\\lpr\\images\\placa_frontal.jpg')
                                    imagem_branca.save('app\\services\\lpr\\images\\placa_traseira.jpg')

                                    lpr = 'N' if tipo == '1' else 'Y'

                                    ultimo_evento.lpr = lpr
                                    ultimo_evento.pesar = "N"
                                    ultimo_evento.placa_1 = placa_frontal
                                    ultimo_evento.placa_2 = placa_traseira
                                    ultimo_evento.pos_fila = None

                                    db.session.commit()
                                except Exception as e:
                                    print(f"Erro ao atualizar o evento: {e}")
                                    return jsonify({"error": "Erro ao atualizar o evento."}), 500

                            novo_check = ProgramacaoCheck(
                                evento_id=evento_id,
                                traseira_progrmacao=carreta_programacao,
                                frontal_programacao=cavalo_programacao,
                                pessoa_programacao=pessoa_programacao,
                                cpf_programacao=cpf_programacao,
                                frontal_detectada=placa_frontal,
                                traseira_detectada=placa_traseira,
                                pessoa_detectada=pessoa,
                                cpf_detectado=cpf_primeiro_da_fila,
                                frontal_corrigida='',
                                traseira_corrigida='',
                                pessoa_corrigida='',
                                cpf_corrigido='',
                                frontal_status=status_frontal,
                                traseira_status=status_traseira,
                                pessoa_status=status_pessoa,
                                cpf_status=status_pessoa,
                                geral_status=status_geral
                            )

                            existing_check = ProgramacaoCheck.query.filter_by(evento_id=evento_id).first()

                            if existing_check is None:
                                db.session.add(novo_check)
                                db.session.commit()
                            else:
                                if status_frontal == "ok":
                                    existing_check.frontal_corrigida = placa_frontal
                                if status_traseira == "ok":
                                    existing_check.traseira_corrigida = placa_traseira
                                if status_pessoa == "ok":
                                    existing_check.pessoa_corrigida = pessoa
                                    existing_check.cpf_corrigido = cpf_primeiro_da_fila

                                existing_check.frontal_detectada = placa_frontal
                                existing_check.traseira_detectada = placa_traseira
                                existing_check.geral_status = status_geral
                                db.session.commit()

                            resultados.append({
                                "direcao": direcao_nome,
                                "placa_frontal": placa_frontal,
                                "placa_traseira": placa_traseira,
                                "pessoa": pessoa,
                                "cpf_primeiro_da_fila": cpf_primeiro_da_fila,
                                "pessoa_programacao": pessoa_programacao,
                                "cpf_programacao": cpf_programacao,
                                "carreta_programacao": carreta_programacao,
                                "cavalo_programacao": cavalo_programacao,
                                "status_frontal": status_frontal,
                                "status_traseira": status_traseira,
                                "status_pessoa": status_pessoa,
                                "status_geral": status_geral
                            })

                        except requests.exceptions.HTTPError as e:
                            print(f"Erro HTTP ao buscar programação: {e}")
                            continue
                        except Exception as e:
                            print(f"Erro ao buscar programação por CPF: {e}")
                            continue

                return jsonify(resultados)

            except Exception as e:
                print(f"Erro ao obter as placas: {e}")
                return jsonify({"error": "Erro ao obter as placas."}), 500

        @self.blueprint.route('/verificar_direcao', methods=['GET'])
        def verificar_direcao(direcao = 0):
            direcao = request.args.get('direcao')   
            print('DIREÇÃO DISPONIVEL: ',direcao)         
            # Verifica se a direção está em uso
            if direcao == "1":  # Direção "ENTRADA DE VEÍCULOS"
                evento_ativo = Evento.query.filter(Evento.direcao == "OUT").first()
                if evento_ativo:
                    return jsonify({'disponivel': 2})  # Direção em uso
            elif direcao == "2":  # Direção "SAÍDA DE VEÍCULOS"
                evento_ativo = Evento.query.filter(Evento.direcao == "IN").first()
                if evento_ativo:
                    return jsonify({'disponivel': 1})  # Direção em uso

            return jsonify({'disponivel': True})  # Direção disponível
        
        @self.blueprint.route('/novo_evento_contingencia', methods=['GET', 'POST'])
        def novo_evento_contingencia():            
            # Obtém os dados enviados como JSON
            data = request.get_json()
            print('Json Recebido: ', data)
            # exit()
            if not data:
                return jsonify({"error": "Invalid or missing JSON data"}), 400
            
            # Extrai os dados do JSON
            direcao = data.get('direcao')
            codigo_erro = data.get('ErrorCode')
            id_equipamento = data.get('UserID')
            id_evento = data.get('CreateTime')
            imagem_path = data.get('URL')
            cpf = data.get('CardNo')
            pessoa = data.get('CardName')
            pos_fila = None  # Defina conforme necessário
            contingencia = "Y"
            
            # Define o valor de 'pesar' com base na direção
            pesar = "N" if direcao == "IN" else "N"  # Se direção for IN, pesar = "Y", caso contrário, pesar = "N"

            # Cria um novo objeto Evento
            novo_evento = Evento(direcao=direcao, codigo_erro=codigo_erro, id_equipamento=id_equipamento, id_evento=id_evento, imagem_path=imagem_path, json=data, cpf=cpf, pessoa=pessoa, pos_fila=pos_fila, pesar=pesar, contingencia=contingencia)

            # Verifica se já existe um evento com o mesmo id_evento
            evento_existente = Evento.query.filter_by(id_evento=id_evento).first()
            
            if evento_existente:
                print("Evento já adicionado")
                return jsonify({"status": "Evento Duplicado!"}), 409  # Conflito

            # Adiciona o novo evento ao banco de dados
            try:
                db.session.add(novo_evento)
                db.session.commit() 
                return jsonify({"status": "Evento inserido com sucesso"}), 201  # Criado
            except Exception as e:
                print(f"Erro ao inserir evento no banco: {e}")
                return jsonify({"error": "Erro ao inserir evento"}), 500  # Erro interno do servidor
            
        # Nova rota para atualizar a posição na fila
        @self.blueprint.route('/eventos/<int:id>/atualizar_pos_fila', methods=['POST'])
        @csrf.exempt  # Usa a instância csrf para desabilitar CSRF nessa rota
        def atualizar_pos_fila(id):
            try:
                # Obtém o evento a ser atualizado
                evento = Evento.query.get_or_404(id)
                print('######Fila: ',id)
                # Busca eventos com pos_fila diferente de None
                eventos_na_fila = Evento.query.filter(Evento.pos_fila != None).all()

                # Se não houver eventos na fila, define a posição como 1
                if not eventos_na_fila:
                    evento.pos_fila = 1
                else:
                    # Encontra a maior posição na fila
                    maior_pos_fila = max(evento.pos_fila for evento in eventos_na_fila)
                    print('######Fila: ',maior_pos_fila)
                    # Atualiza a posição do evento para o próximo valor disponível
                    evento.pos_fila = maior_pos_fila + 1

                # Salva as alterações no banco de dados
                db.session.commit()
                return jsonify({"status": "success", "message": "Posição na fila atualizada com sucesso"}), 200
            except Exception as e:
                print(f"Erro ao atualizar posição na fila: {e}")
                traceback.print_exc()
                return jsonify({"status": "error", "message": "Erro ao atualizar posição na fila"}), 500
