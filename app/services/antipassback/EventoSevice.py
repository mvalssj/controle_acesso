import requests
from datetime import datetime, timedelta
import time
import os
import sys
import threading
import app
from flask_injector import inject
from app.controllers import EventoController


# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
# from config import device_ip_in, device_ip_out, device_ip_in_truck, device_ip_out_truck, device_ip_out_car, device_ip_in_car, username, password

class EventRecorder:
    def __init__(self, device_ip_in, username, password, direction):
        self.device_ip_in = device_ip_in
        self.username = username
        self.password = password
        self.direction = direction
        self.evento_controller = app.equipamento_controller # Recebe a instância injetada

    def fetch_records(self):
        end_time = int(datetime.now().timestamp())
        start_time = int((datetime.now() - timedelta(hours=0.10)).timestamp())
        url = f"http://{self.device_ip_in}/cgi-bin/recordFinder.cgi?action=find&name=AccessControlCardRec&StartTime={start_time}&EndTime={end_time}"
        digest_auth = requests.auth.HTTPDigestAuth(self.username, self.password)
        rval = requests.get(url, auth=digest_auth)
        return rval.text.splitlines()
        
    def send_records(self, lines):
        record = {}
        current_record_number = None
        for i, line in enumerate(lines):
            line = line.strip()
            if line.startswith('records['):
                key, value = line.split('=', 1)
                record_number = int(key.split('[')[1].split(']')[0])
                if current_record_number is None:
                    current_record_number = record_number
                if record_number != current_record_number:
                    # Se o número do registro mudou, envie o registro atual e reinicie
                    if len(record) == 25:
                        self.send_record(record)
                    record = {}
                    current_record_number = record_number
                key = key.split('.', 1)[1]
                value = value.strip()
                record[key] = value
                # Quando temos 25 campos preenchidos, enviamos como JSON
                if len(record) == 25:
                    record['direcao'] = self.direction  # Add direction to the record
                    self.send_record(record)
                    record = {}
                    current_record_number = None  # Reinicie o número do registro atual
            # Adicione esta condição para garantir que o loop continue mesmo se o número de campos for diferente de 25
            # elif line.startswith('records['):
            #     record = {}  # Reinicia o registro se encontrar um novo conjunto de dados

    def send_record(self, record):
        # print("Record: ", record)

        try:
            response = requests.post(
                'http://127.0.0.1/webhook/evento',
                json=record,  # Envia o record como JSON
                timeout=20
            )
            if response.status_code == 200:
                sucesso = 1
            else:
                print(f"Falha ao enviar o registro: {response.status_code}")
                self.send_record(record)
                # Tenta reenviar o registro atual e os subsequentes em caso de falha
                # self.send_records(lines[i:]) 
                # return # Sai da função após tentar reenviar
        except requests.RequestException as e:
            print(f"Erro ao enviar o registro: {e}")
            self.send_record(record)
            # Tenta reenviar o registro atual e os subsequentes em caso de erro
            # self.send_records(lines[i:])
            # return # Sai da função após tentar reenviar
        finally:
            record = {}  # Reinicia o registro para o próximo conjunto de dados, mesmo em caso de erro

    def run(self):
        while True:
            lines = self.fetch_records()
            print("Aguardando Biometria...", self.device_ip_in)
            self.send_records(lines)
            time.sleep(1)
