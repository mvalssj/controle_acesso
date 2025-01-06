import subprocess
import time
import os
from datetime import datetime

def backup_database():
    # Definir os parâmetros do banco de dados
    db_host = "192.168.9.5"  # Ou o IP do servidor MariaDB
    db_user = "root"
    db_password = "cablev35"
    db_name = "controle_acesso"
    
    # Definir o diretório onde os backups serão armazenados
    backup_dir = "\\\\192.168.9.1\\iacesso"  # Diretório na rede (usar quatro barras para escape correto)
    if not os.path.exists(backup_dir):
        try:
            os.makedirs(backup_dir)  # Criar o diretório se não existir
        except OSError as e:
            print(f"Erro ao criar diretório: {e}")
            return
    
    # Definir o nome do arquivo de backup com base na data e hora atuais
    backup_file = os.path.join(backup_dir, f"backup_{db_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql")
    
    # Comando para fazer o dump do banco de dados
    dump_command = [
        "C:\\xampp2\\mysql\\bin\\mysqldump",  # Caminho completo para o mysqldump,
        f"--host={db_host}",
        f"--user={db_user}",
        f"--password={db_password}",
        db_name,
        "--routines",  # Para incluir procedures e funções
        "--events",  # Para incluir eventos do banco
        "--triggers"  # Para incluir triggers
    ]
    
    try:
        # Abrir o arquivo para gravar o backup
        with open(backup_file, "w") as f:
            # Executar o comando mysqldump e redirecionar a saída para o arquivo
            subprocess.run(dump_command, stdout=f, check=True)
        print(f"Backup do banco de dados '{db_name}' concluído com sucesso em {backup_file}")
    except (OSError, subprocess.CalledProcessError) as e:
        print(f"Erro ao executar o backup: {e}")

# Função principal para agendar o backup a cada 1 hora
def schedule_backup():
    while True:
        backup_database()
        # Esperar 1 hora (3600 segundos) antes de fazer o próximo backup
        time.sleep(3600)

if __name__ == "__main__":
    schedule_backup()