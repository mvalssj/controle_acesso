import builtins  # Para manipular o print original
import logging
import os
import sys
import time
import subprocess
from multiprocessing import Process
from threading import Thread

from app import app
from app.controllers.EquipamentoController import EquipamentoController
from app.helpers.task_manager import ProcessMonitor
from app.services.antipassback.EventoSevice import EventRecorder
from config import unidade, username, password

# 1) Guardar o print original
original_print = builtins.print

# 2) Criar uma função "no_print" que não faz nada
def no_print(*args, **kwargs):
    pass

# 3) Redirecionar o print global para no_print
# builtins.print = no_print

# =================================================================
# Configuração de LOG apenas em arquivo
# =================================================================

log_file = os.path.join(os.path.dirname(__file__), 'app.log')

root_logger = logging.getLogger()
root_logger.handlers.clear()

file_handler = logging.FileHandler(log_file, mode='a')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s - %(lineno)d - %(message)s')
file_handler.setFormatter(formatter)

root_logger.addHandler(file_handler)
root_logger.setLevel(logging.DEBUG)

logging.getLogger('werkzeug').disabled = True
if hasattr(app, 'logger'):
    app.logger.disabled = True

# =================================================================
# Funções
# =================================================================

def run_event_recorder_process(ip, username, password, tipo, process_name):
    try:
        logging.info(f"Iniciando processo {process_name}")
        recorder = EventRecorder(ip, username, password, tipo)
        recorder.run()
        logging.info(f"Processo {process_name} encerrado.")
    except Exception as e:
        logging.exception(f"Erro no processo {process_name}: {e}")

def restart_process(process_name, ip, username, password, tipo):
    logging.info(f"Reiniciando processo {process_name}...")
    new_process = Process(
        target=run_event_recorder_process,
        args=(ip, username, password, tipo, process_name)
    )
    new_process.start()
    # Se reiniciar mostra o processo novamente
    monitor_thread = Thread(target=run_monitor, args=(process_monitor,), daemon=True)
    monitor_thread.start()
    return new_process

def run_flask():
    logging.info("Iniciando servidor Flask...")
    app.run(host='0.0.0.0', debug=False, port=80, use_reloader=False)

def run_movimento_service():
    try:
        logging.info("Iniciando MovimentoService...")
        path_to_script = os.path.abspath("app\\services\\movimento\\MovimentoService.py")
        path_to_python = sys.executable
        with open(log_file, 'a') as log_file_handler: # Redireciona stdout e stderr para o arquivo de log
            process = subprocess.Popen([path_to_python, path_to_script], stdout=log_file_handler, stderr=log_file_handler)
            return process
    except FileNotFoundError:
        logging.error("Erro: MovimentoService.py não encontrado.")
        return None
    except Exception as e:
        logging.exception(f"Erro ao iniciar MovimentoService: {e}")
        return None

def run_monitor(process_monitor):
    """
    Executa o ProcessMonitor em uma thread separada,
    restaurando temporariamente o print original para exibir a tabela.
    """
    try:
        logging.info("Iniciando monitoramento de processos...")
        # 4) Restaurar print original DENTRO do monitor()
        import builtins
        old_print = builtins.print
        builtins.print = original_print  # permite prints só aqui

        # Agora, qualquer print dentro de process_monitor.monitor() aparecerá no terminal
        process_monitor.monitor()

    except Exception as e:
        logging.exception(f"Erro crítico no monitoramento de processos: {e}")
        # Reinicia o monitoramento caso ocorra um erro crítico
        time.sleep(5) # Espera um pouco antes de tentar novamente
        run_monitor(process_monitor) # Chama a si mesma recursivamente para reiniciar

    finally:
        # 5) Volta ao no_print para silenciar prints fora do monitor()
        builtins.print = old_print
        logging.info("Monitoramento de processos encerrado.")

# =================================================================
# Main
# =================================================================

if __name__ == '__main__':
    equipamento_controller = EquipamentoController()
    movimento_process = None
    flask_process = None

    flask_process = Process(target=run_flask)
    flask_process.start()
    logging.info(f"Processo Flask iniciado com PID: {flask_process.pid}")

    biometria_processes = {}
    started_processes = set()

    with app.app_context():
        ips_entrada, ips_saida = equipamento_controller.get_equipamento_id(unidade)

    process_monitor = ProcessMonitor()

    for ip_entrada in ips_entrada:
        for ip_saida in ips_saida:
            process_in_name = f"Biometria_in_{ip_entrada}"
            process_out_name = f"Biometria_out_{ip_saida}"

            if process_in_name not in started_processes:
                proc_in = Process(
                    target=run_event_recorder_process,
                    args=(ip_entrada, username, password, 'IN', process_in_name)
                )
                proc_in.start()
                biometria_processes[process_in_name] = {
                    "process": proc_in,
                    "ip": ip_entrada,
                    "tipo": "IN"
                }
                started_processes.add(process_in_name)
                logging.info(f"Processo {process_in_name} iniciado com PID: {proc_in.pid}")
                process_monitor.add_process(proc_in.pid, f"Biometria - {process_in_name}")

            if process_out_name not in started_processes:
                proc_out = Process(
                    target=run_event_recorder_process,
                    args=(ip_saida, username, password, 'OUT', process_out_name)
                )
                proc_out.start()
                biometria_processes[process_out_name] = {
                    "process": proc_out,
                    "ip": ip_saida,
                    "tipo": "OUT"
                }
                started_processes.add(process_out_name)
                logging.info(f"Processo {process_out_name} iniciado com PID: {proc_out.pid}")
                process_monitor.add_process(proc_out.pid, f"Biometria - {process_out_name}")

    movimento_process = run_movimento_service()
    if movimento_process:
        logging.info(f"MovimentoService iniciado com PID: {movimento_process.pid}")
        time.sleep(1)

    if flask_process:
        process_monitor.add_process(flask_process.pid, "Flask")
    if movimento_process:
        process_monitor.add_process(movimento_process.pid, "MovimentoService")

    monitor_thread = Thread(target=run_monitor, args=(process_monitor,), daemon=True)
    # monitor_thread.start()
    logging.info("Thread de monitoramento iniciada.")

    while True:
        try:
            if movimento_process and movimento_process.poll() is not None:
                logging.warning("MovimentoService encerrado inesperadamente. Reiniciando...")
                movimento_process = run_movimento_service()
                if movimento_process:
                    logging.info(f"MovimentoService reiniciado com PID: {movimento_process.pid}")

            if flask_process and flask_process.poll() is not None:
                logging.warning("Processo Flask encerrado inesperadamente. Reiniciando...")
                flask_process = Process(target=run_flask)
                flask_process.start()
                logging.info(f"Processo Flask reiniciado com PID: {flask_process.pid}")

            for process_name, data in list(biometria_processes.items()):
                proc = data["process"]
                ip = data["ip"]
                tipo = data["tipo"]
                if not proc.is_alive():
                    logging.warning(f"Processo {process_name} encerrado inesperadamente. Reiniciando...")
                    new_proc = restart_process(process_name, ip, username, password, tipo)
                    biometria_processes[process_name]["process"] = new_proc
                    logging.info(f"Processo {process_name} reiniciado com PID: {new_proc.pid}")
                    process_monitor.add_process(new_proc.pid, f"Biometria - {process_name}")

            time.sleep(5)

        except KeyboardInterrupt:
            logging.info("Programa encerrado pelo usuário.")
            break
        except Exception as e:
            logging.exception(f"Erro crítico no loop principal: {e}")
            # Adiciona um tratamento de exceção mais robusto para o loop principal
            time.sleep(60) # Espera 1 minuto antes de tentar novamente
            # Não precisa reiniciar o loop principal, pois ele já faz isso automaticamente

    logging.info("Encerrando o programa...")
    if movimento_process:
        movimento_process.terminate()
    if flask_process:
        flask_process.terminate()
    for data in biometria_processes.values():
        data["process"].terminate()
    monitor_thread.join()
    for data in biometria_processes.values():
        data["process"].join()