import logging
import time
from rich.live import Live
from rich.table import Table
import psutil

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ProcessMonitor:
    def __init__(self):
        self.processes = []  # Lista para armazenar tuplas (PID, nome_serviço)

    def add_process(self, pid, service_name):
        """Adiciona um processo ao monitor, dado o seu PID e nome do serviço."""
        try:
            process = psutil.Process(pid)
            self.processes.append((process, service_name))
            logging.info(f"Processo {service_name} com PID {pid} adicionado ao monitor.")
        except psutil.NoSuchProcess:
            logging.error(f"Processo com PID {pid} não encontrado.")

    def generate_table(self):
        table = Table(title="Gerenciador de Tarefas")
        table.add_column("PID")
        table.add_column("Serviço")
        table.add_column("Nome")
        table.add_column("Status")
        table.add_column("CPU (%)")
        table.add_column("Memória (%)")

        for process, service_name in self.processes:
            try:
                status = "Rodando" if process.is_running() else "Finalizado"
                cpu_percent = process.cpu_percent()
                memory_percent = process.memory_percent()
                table.add_row(str(process.pid), service_name, process.name(), status, str(cpu_percent), str(memory_percent))
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                logging.warning(f"Erro ao obter informações do processo {process.pid}. Removendo do monitor.")
                self.processes.remove((process, service_name))

        return table

    def monitor(self):
        with Live(self.generate_table(), refresh_per_second=4, screen=True) as live:
            while self.processes:
                try:
                    live.update(self.generate_table())
                    time.sleep(1)
                except KeyboardInterrupt:
                    logging.info("Monitoramento interrompido pelo usuário.")
                    break
                except Exception as e:
                    logging.exception(f"Erro no monitoramento: {e}")
        logging.info("Monitoramento finalizado.")
