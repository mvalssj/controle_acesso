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
        process = subprocess.Popen(["%LOCALAPPDATA%//Programs//Python//Python310//python.exe", "C:\\controle_acesso\\app\\services\\movimento\\MovimentoService.py"], shell=True)
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

    # Dicionário para armazenar as threads e seus respectivos recorders
    threads = {}

    # Conjunto para rastrear os nomes das threads já iniciadas
    started_threads = set()

    # Captura o ip das biometrias            
    with app.app_context():
        ips_entrada, ips_saida = equipamento_controller.get_equipamento_id(unidade)

    # Itera sobre os IPs de entrada e saída
    for ip_entrada in ips_entrada:
        for ip_saida in ips_saida:
            # Cria instâncias de EventRecorder
            recorder1 = EventRecorder(ip_entrada, username, password, 'IN')
            recorder2 = EventRecorder(ip_saida, username, password, 'OUT')

            # Gera nomes únicos para as threads
            thread_in_name = f"Biometria_in_{ip_entrada}"
            thread_out_name = f"Biometria_out_{ip_saida}"

            # Verifica se a thread já foi iniciada
            if thread_in_name not in started_threads:
                # Inicia as threads e adiciona-as ao conjunto
                thread_in = Thread(target=run_event_recorder, args=(recorder1, thread_in_name), daemon=True)
                threads[thread_in_name] = thread_in
                thread_in.start()
                started_threads.add(thread_in_name)

            if thread_out_name not in started_threads:
                thread_out = Thread(target=run_event_recorder, args=(recorder2, thread_out_name), daemon=True)
                threads[thread_out_name] = thread_out
                thread_out.start()
                started_threads.add(thread_out_name)
    
        # Não precisa mais do restart_thread aqui
    movimento_process = run_movimento_service()
    if movimento_process:
        logging.info(f"MovimentoService iniciado com PID: {movimento_process.pid}")
        # Adicione um pequeno delay para evitar sobrecarga
        time.sleep(1)  # Espera 1 segundo antes de processar o próximo

    while True:
        try:
            # Verificação e reinicialização do processo de movimento
            if movimento_process and movimento_process.poll() is not None:
                logging.warning("MovimentoService encerrado inesperadamente. Reiniciando...")
                movimento_process = run_movimento_service()
                if movimento_process:
                    logging.info(f"MovimentoService reiniciado com PID: {movimento_process.pid}")

            # Verificação e reinicialização das threads
            for thread_name, thread in threads.items():
                if not thread.is_alive():
                    logging.warning(f"Thread {thread_name} encerrada inesperadamente. Reiniciando...")
                    if "in" in thread_name:
                        ip = ip_entrada
                        tipo = 'IN'
                    else:
                        ip = ip_saida
                        tipo = 'OUT'
                    recorder = EventRecorder(ip, username, password, tipo)
                    threads[thread_name] = restart_thread(thread, recorder, thread_name)

            time.sleep(5)  # Espera por 5 segundos antes de verificar novamente

        except KeyboardInterrupt:
            logging.info("Programa encerrado pelo usuário.")
            break
        except Exception as e:
            logging.exception(f"Erro no loop principal: {e}")
            time.sleep(5)  # Espera por 5 segundos antes de tentar novamente

    logging.info("Encerrando o programa...")
