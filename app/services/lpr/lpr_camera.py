import requests
import os
from requests.auth import HTTPDigestAuth
from PIL import Image
import subprocess
import sys, os

# Obtém o caminho absoluto do diretório do script atual
dir_atual = os.path.dirname(os.path.abspath(__file__))
# Obtém o caminho absoluto do diretório três níveis acima
dir_raiz = os.path.dirname(os.path.dirname(os.path.dirname(dir_atual)))

# Adiciona o diretório raiz ao caminho de busca do Python
if dir_raiz not in sys.path:
    sys.path.insert(0, dir_raiz)

# Agora você pode importar o módulo config
import config

# Verifica se algum argumento foi passado para o script
if len(sys.argv) > 1:
    tipo_placa = sys.argv[1]
    print(f"Tipo de placa recebido: {tipo_placa}")

    if tipo_placa == "balanca_traseira": # Correção: Comparação direta com a string
        camera_url = config.camera_placa_traseira_balanca
        pasta_imagens = "app\\services\\lpr\\images\\"
        foto_placa = "placa_traseira.jpg"
        file_placa = "placa_traseira_balanca.txt"
    elif tipo_placa == "balanca_frontal":
        print("Usando placa frontal.")
        camera_url = config.camera_placa_frontal_balanca # URL da câmera padrão (placa frontal)
        pasta_imagens = "app\\services\\lpr\\images\\" # Pasta de imagens padrão
        foto_placa = "placa_frontal.jpg" # grava a foto da placa
        file_placa = "placa_frontal_balanca.txt" # grava o texto da balanca
else:
    print('Nenhum argumento passado...')
    camera_url = config.camera_entrada_pedestre # URL da câmera padrão (placa frontal)
    pasta_imagens = "app\\services\\lpr\\images\\" # Pasta de imagens padrão
    foto_placa = "live.jpg" # grava a foto da placa
    file_placa = "placa_frontal.txt" # grava o texto da entrada

def save_image_from_url(url, filepath, username, password):
    """
    Faz o download de uma imagem de uma URL e salva em um arquivo especificado, com autenticação Digest.
    """
    try:
        auth = HTTPDigestAuth(username, password)
        response = requests.get(url, auth=auth, stream=True)
        response.raise_for_status()

        with open(filepath, 'wb') as out_file:
            for chunk in response.iter_content(chunk_size=8192):
                out_file.write(chunk)        
        # print(f"Imagem salva com sucesso em: {filepath}")
    except requests.exceptions.RequestException as e:
        # print(f"Erro ao baixar a imagem: {e}")
        erro = 1
    except Exception as e:
        erro = 1
        # print(f"Erro ao salvar a imagem: {e}")


def crop_image(input_path, output_path, top_crop_cm, left_crop_cm, right_crop_cm, dpi):
    """Recorta a parte superior e os lados de uma imagem."""
    try:
        img = Image.open(input_path)
        width, height = img.size
        pixels_per_inch = dpi
        pixels_per_cm = pixels_per_inch / 2.54
        top_crop_pixels = int(top_crop_cm * pixels_per_cm)
        left_crop_pixels = int(left_crop_cm * pixels_per_cm)
        right_crop_pixels = int(right_crop_cm * pixels_per_cm)
        cropped_img = img.crop((left_crop_pixels, 0, width - right_crop_pixels, top_crop_pixels)) #Modificação aqui
        cropped_img.save(output_path)
        # print(f"Imagem recortada salva com sucesso em: {output_path}")
    except FileNotFoundError:
        erro = 1
        # print(f"Erro: Arquivo de imagem não encontrado: {input_path}")
    except Exception as e:
        erro = 1
        # print(f"Erro ao recortar a imagem: {e}")

if len(sys.argv) > 1:
    if tipo_placa == "balanca_frontal":
        ip_lpr = config.device_ip_lpr_frente
        placa = "string_frontal.jpg"
    elif tipo_placa == "balanca_traseira":
        ip_lpr = config.device_ip_lpr_fundo
        placa = "string_traseira.jpg"
else:
    ip_lpr = config.device_ip_lpr_entrada
    placa = "string_entrada.jpg"

if __name__ == "__main__":
    url = f"http://{ip_lpr}/cgi-bin/snapManager.cgi?action=attachFileProc&channel=1&heartbeat=1&Flags[0]=Event&Events=[TrafficManualSnap]"
    base_path = "C:\\controle_acesso\\app\\services\\lpr\\images"
    username = config.username
    password = config.password
    dpi = 300 # Defina a resolução em DPI da sua imagem

    # Salvando a primeira imagem
    image_path1 = os.path.join(base_path, foto_placa)
    save_image_from_url(url, image_path1, username, password)

    # Recortando e salvando a segunda imagem
    image_path2 = os.path.join(base_path, placa)
    crop_image(image_path1, image_path2, 0.3, 2.14, 13.1, dpi)
    try:
        # print('File Placa: ',file_placa)
        subprocess.run(["python", "app\\services\\lpr\\api_lpr_offline.py", foto_placa, file_placa])
        # print("Subprocesso executado com sucesso.")
    except subprocess.CalledProcessError as e:
        erro = 1
        # print(f"Erro ao executar o subprocesso: Retorno {e.returncode}, Saída de erro: {e.stderr.decode()}")
    except FileNotFoundError:
        erro = 1
        # print(f"Erro: Arquivo 'api_lpr_offline.py' não encontrado.")
    except Exception as e:
        erro = 1
        # print(f"Erro inesperado ao executar o subprocesso: {e}")