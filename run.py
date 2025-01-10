from app import app
from app.services.antipassback.EventoSevice import EventRecorder
from app.controllers.EquipamentoController import EquipamentoController # Importe o controlador
from threading import Thread
import os
import sys
import time
import subprocess
from multiprocessing import Process
import logging

# Adiciona o caminho do diretório pai ao PATH do sistema, permitindo importar módulos de outros diretórios
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from config import unidade, username, password

# Configura o logging para melhor monitoramento
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_event_recorder(recorder, thread_name):
    """
    Função para executar o EventRecorder em uma thread separada.
    Esta função encapsula a execução do EventRecorder, tratando possíveis exceções.
    """
    try:
        logging.info(f"Iniciando thread {thread_name}")
        recorder.run()  # Executa o método run() do objeto EventRecorder
        logging.info(f"Thread {thread_name} encerrada.")
    except Exception as e:
        logging.exception(f"Erro na thread {thread_name}: {e}")  # Imprime qualquer erro ocorrido durante a execução

def restart_thread(thread, recorder, thread_name):
    """
    Função para reiniciar uma única thread.
    Cria uma nova thread para executar o EventRecorder, substituindo a thread anterior se necessário.
    """
    logging.info(f"Reiniciando thread {thread_name}...")
    if thread and thread.is_alive():
        logging.warning(f"Thread {thread_name} ainda está ativa. Tentando juntar...")
        thread.join() # Tenta esperar a thread terminar antes de criar uma nova.
    new_thread = Thread(target=run_event_recorder, args=(recorder, thread_name), daemon=True)
    new_thread.start()  # Inicia a nova thread
    return new_thread

def run_flask():
    """
    Função para rodar o servidor Flask.
    Esta função inicia o servidor Flask, que é responsável pela interface web da aplicação.
    """
    logging.info("Iniciando servidor Flask...")
    app.run(host='0.0.0.0', debug=False, port=80)

def run_movimento_service():
    """
    Função para executar o MovimentoService em um processo separado.
    Esta função inicia o serviço de detecção de movimento em um processo separado, para melhor isolamento e gerenciamento.
    """
    try:
        logging.info("Iniciando MovimentoService...")
        process = subprocess.Popen(["python", "app\\services\\movimento\\MovimentoService.py"], shell=True)
        return process
    except FileNotFoundError:
        logging.error("Erro: MovimentoService.py não encontrado.")
        return None
    except Exception as e:
        logging.exception(f"Erro ao iniciar MovimentoService: {e}")
        return None

if __name__ == '__main__':
        # Instancia o controlador
    equipamento_controller = EquipamentoController()
    biometria_in_pedestre = None
    biometria_out_pedestre = None
    movimento_process = None  # Variável para armazenar o processo do MovimentoService

    # Inicia o servidor Flask em um processo separado (opcional, mas recomendado para melhor isolamento)
    flask_process = Process(target=run_flask)
    flask_process.start()
    logging.info(f"Processo Flask iniciado com PID: {flask_process.pid}")

    # Captura o ip das biometrias            
    with app.app_context():
        ips_entrada, ips_saida = equipamento_controller.get_equipamento_id(unidade)
    # Itera sobre os IPs de entrada e saída
    for ip_entrada in ips_entrada:
        # print('##IP Entrada:', ip_entrada)
        device_ip_in = ip_entrada
        for ip_saida in ips_saida:
            device_ip_out = ip_saida
            # print('##IP Saída:', ip_saida)

            # Cria instâncias de EventRecorder para entrada e saída
            recorder1 = EventRecorder(device_ip_in, username, password, 'IN')
            print('Recorder de Entrada: ',device_ip_in)
            recorder2 = EventRecorder(device_ip_out, username, password, 'OUT')
            print('Recorder de Saída: ',device_ip_out)
            # Inicia a detecção de movimento como um processo separado

            movimento_process = run_movimento_service()
            if movimento_process:
                logging.info(f"MovimentoService iniciado com PID: {movimento_process.pid}")

            # Inicia as threads dos EventRecorders
            biometria_in_pedestre = restart_thread(biometria_in_pedestre, recorder1, "Biometria_in_pedestre")
            biometria_out_pedestre = restart_thread(biometria_out_pedestre, recorder2, "Biometria_out_pedestre")

    while True:
        try:
            # Verificação e reinicialização do processo de movimento (não há necessidade de verificar as threads, pois são daemons)
            if movimento_process and movimento_process.poll() is not None:
                logging.warning("MovimentoService encerrado inesperadamente. Reiniciando...")
                movimento_process = run_movimento_service()
                if movimento_process:
                    logging.info(f"MovimentoService reiniciado com PID: {movimento_process.pid}")

            time.sleep(5)  # Espera por 5 segundos antes de verificar novamente

        except KeyboardInterrupt:
            logging.info("Programa encerrado pelo usuário.")
            break
        except Exception as e:
            logging.exception(f"Erro no loop principal: {e}")
            time.sleep(5)  # Espera por 5 segundos antes de tentar novamente

    logging.info("Encerrando o programa...")
