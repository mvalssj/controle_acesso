import os
import sys
import cv2
import time
import subprocess

# Obtém o caminho absoluto do diretório do script atual
dir_atual = os.path.dirname(os.path.abspath(__file__))
# Obtém o caminho absoluto do diretório três níveis acima
dir_raiz = os.path.dirname(os.path.dirname(os.path.dirname(dir_atual)))

# Adiciona o diretório raiz ao caminho de busca do Python
if dir_raiz not in sys.path:
    sys.path.insert(0, dir_raiz)

# Agora você pode importar o módulo config
# Removido o print e o exit
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
    else: # bloco else adicionado para o caso da placa frontal
        print("Usando placa frontal.")
        camera_url = config.camera_placa_frontal_balanca # URL da câmera padrão (placa frontal)
        pasta_imagens = "app\\services\\lpr\\images\\" # Pasta de imagens padrão
        foto_placa = "placa_frontal.jpg" # grava a foto da placa
        file_placa = "placa_frontal_balanca.txt" # grava o texto da balanca

else:
    camera_url = config.camera_entrada_pedestre # URL da câmera padrão (placa frontal)
    pasta_imagens = "app\\services\\lpr\\images\\" # Pasta de imagens padrão
    foto_placa = "live.jpg" # grava a foto da placa
    file_placa = "placa_frontal.txt" # grava o texto da balanca
# Inicializar o VideoCapture
cap = cv2.VideoCapture(camera_url, cv2.CAP_FFMPEG)

# Verificar se o fluxo foi aberto com sucesso
if not cap.isOpened():
    print("Erro ao abrir o fluxo.")
    exit()

# Definir o intervalo de tempo para tirar uma foto (5 segundos)
intervalo_foto = 1

# Inicializar um contador de tempo para tirar fotos
tempo_anterior = time.time()

# Loop principal
while True:
    ret, frame = cap.read()

    # Verificar se é hora de tirar uma foto (a cada 5 segundos)
    tempo_atual = time.time()
    if tempo_atual - tempo_anterior >= intervalo_foto:
        caminho_imagem = pasta_imagens + foto_placa
        # Ler o frame
        ret, frame = cap.read()
        # Obter as dimensões do frame
        height, width = frame.shape[:2]
        # Calcular as coordenadas do centro
        center_x, center_y = width // 2, height // 2
        # Calcular as novas dimensões com zoom de 4x
        new_width, new_height = width // 2, height // 2
        # Calcular as coordenadas do canto superior esquerdo para o recorte
        x1 = center_x - new_width // 2
        y1 = center_y - new_height // 2
        x2 = x1 + new_width
        y2 = y1 + new_height
        # Recortar o frame
        cropped_frame = frame[y1:y2, x1:x2]
        # Redimensionar o frame recortado para o tamanho original (zoom de 4x)
        resized_frame = cv2.resize(cropped_frame, (width, height), interpolation=cv2.INTER_CUBIC)
        # Salvar a imagem com zoom
        cv2.imwrite(caminho_imagem, resized_frame)
        print(f"Imagem salva em {caminho_imagem}")
        tempo_anterior = tempo_atual   

        # Executar o api.py após salvar a imagem, passando as variáveis como argumentos
        subprocess.call(["python", "app\\services\\lpr\\api.py", foto_placa, file_placa])

        break

    # Verificar se o usuário pressionou 'q' para sair
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Liberar recursos
cap.release()
cv2.destroyAllWindows()
