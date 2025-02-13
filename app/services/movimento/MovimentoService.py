import cv2
import subprocess
import time
import threading
import requests
from PIL import Image
import os
import sys

# Obtém o caminho absoluto do diretório do script atual
dir_atual = os.path.dirname(os.path.abspath(__file__))
# Obtém o caminho absoluto do diretório três níveis acima
dir_raiz = os.path.dirname(os.path.dirname(os.path.dirname(dir_atual)))

# Adiciona o diretório raiz ao caminho de busca do Python
if dir_raiz not in sys.path:
    sys.path.insert(0, dir_raiz)

# Agora você pode importar o módulo config
import config

camera = config.device_ip_lpr_fundo
username = config.username
password = config.password

class Movimento:
    def __init__(self, camera_url, largura=320, altura=240, x1=240, y1=180, x2=620, y2=250, area_minima_contorno=100):
        # Inicializa a URL da câmera, largura, altura e outras configurações. usar 10
        self.camera_url = camera_url
        self.largura = largura
        self.altura = altura
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.area_minima_contorno = area_minima_contorno
        # Inicializa o objeto VideoCapture.
        self.cap = cv2.VideoCapture(self.camera_url)
        # Inicializa o frame anterior como None.
        self.frame_anterior = None

        # Verifica se a câmera foi aberta com sucesso.
        if not self.cap.isOpened():
            print("Erro ao abrir a câmera.")
            exit()

        # Define a largura e altura do frame.
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.largura)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.altura)

    def detectar_movimento(self):
        tempo_ultima_deteccao = 0
        ultima_direcao = None  # Armazena a última direção detectada
        em_deteccao = False
        contagem_entrada = 0
        contagem_saida = 0
        primeira_deteccao = True  # Flag para a primeira detecção
        

        while True:
            ret, frame = self.cap.read()
            if not ret:
                # print("Erro ao ler o frame.")
                break

            cv2.rectangle(frame, (self.x1, self.y1), (self.x2, self.y2), (0, 0, 255), 2)
            frame_cinza = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            roi = frame_cinza[self.y1:self.y2, self.x1:self.x2]
            roi = cv2.GaussianBlur(roi, (21, 21), 0)

            if self.frame_anterior is None:
                self.frame_anterior = roi
                continue

            diferenca_frame = cv2.absdiff(self.frame_anterior, roi)
            _, thresh = cv2.threshold(diferenca_frame, 25, 255, cv2.THRESH_BINARY)
            thresh = cv2.dilate(thresh, None, iterations=2)
            contornos, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            movimento_detectado = False

            for contorno in contornos:
                if cv2.contourArea(contorno) < self.area_minima_contorno:
                    continue

                (x, y, w, h) = cv2.boundingRect(contorno)

                centro_x = x + w // 2 + self.x1
                centro_y = y + h // 2 + self.y1

                if self.x1 < centro_x < self.x2 and self.y1 < centro_y < self.y2:
                    if centro_y < (self.y1 + self.y2) // 2:
                        direcao = "Entrada"
                        contagem_entrada += 1
                        contagem_saida = 0
                    else:
                        direcao = "Saída"
                        contagem_saida += 1
                        contagem_entrada = 0
                else:
                    direcao = "Indefinido"
                    contagem_entrada = 0
                    contagem_saida = 0

                # print("####### Momento de usar o LPR #######")
                # threading.Thread(target=self.executar_lpr).start()    
                # timer_lpr = threading.Timer(20, self.executar_lpr) # Cria um timer para executar executar_lpr a cada 20 segundos
                # timer_lpr.start() # Inicia o timer      

                if direcao == "Entrada" and contagem_entrada >= 2 and not em_deteccao:
                    # print("####### Momento de usar o LPR #######")
                    threading.Thread(target=self.executar_lpr).start()
                    em_deteccao = True
                    contagem_entrada = 0

                elif direcao == "Saída" and contagem_saida >= 2:
                    # print("####### Momento de usar o LPR #######")
                    # threading.Thread(target=self.executar_lpr).start()
                    # em_deteccao = True
                    contagem_saida = 0

                if primeira_deteccao:
                    ultima_direcao = direcao
                    primeira_deteccao = False

                if ultima_direcao != direcao:
                    # if direcao == "Entrada":
                    #     print("Veículo entrando")
                    # elif direcao == "Saída":
                    #     print("Veículo saindo")
                    ultima_direcao = direcao

                cv2.rectangle(frame, (x + self.x1, y + self.y1), (x + w + self.x1, y + h + self.y1), (0, 255, 0), 2)
                movimento_detectado = True
                
            if not movimento_detectado:
                em_deteccao = False
                contagem_entrada = 0
                contagem_saida = 0

            if movimento_detectado:
                movimento = 1
                # print("Movimento detectado!")
            # else:
            #     print("Sem movimento")

            # Mostra o video 
            # cv2.imshow("Detecção de Movimento", cv2.resize(frame, (800, 600)))
            self.frame_anterior = roi

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.cap.release()
        cv2.destroyAllWindows()

    def executar_lpr(self):
        """Executa o script lpr_camera.py como um subprocesso em uma thread separada."""
        try:
            for tipo_placa in ["balanca_traseira", "balanca_frontal"]:
                subprocess.run(["python", "C:\\controle_acesso\\app\\services\\lpr\\lpr_camera.py", tipo_placa]) # adicionado timeout para 

            try:
                resposta = requests.get('http://127.0.0.1/checa_placas', params={'tipo': 1}, timeout=5)
                resposta.raise_for_status()  # Lança uma exceção para códigos de status HTTP de erro (4xx ou 5xx)

                dados = resposta.json() # Converte a resposta para JSON

                if dados['status_geral'] == 'ok': # Verifica se o status_geral é "ok"
                    # Após a validação, escreve "N/A" nos arquivos de placa
                    with open('app\\services\\lpr\\placa_frontal_balanca.txt', 'w') as f:
                        f.write("N/A")
                    with open('app\\services\\lpr\\placa_traseira_balanca.txt', 'w') as f:
                        f.write("N/A")

                    # Cria uma imagem branca
                    imagem_branca = Image.new("RGB", (1280, 720), "white")
                    # Salva a imagem branca sobre as imagens existentes
                    imagem_branca.save('app\\services\\lpr\\images\\placa_frontal.jpg')
                    imagem_branca.save('app\\services\\lpr\\images\\placa_traseira.jpg')

                # print('Resposta do request /checa_placas:', resposta.text)
                # print("###### Request /checa_placas executado com sucesso ######")
                return "Novas fotos das placas da balança capturadas e processadas com sucesso! Request /checa_placas executado.", 200

            except requests.exceptions.RequestException as e:
                erro = 1
                # print(f"Erro ao executar o request /checa_placas: {e}")
                # return "Erro ao executar o request /checa_placas após capturar as fotos.", 500

        except Exception as e:
            erro = 1
            # print(f"Erro ao executar o subprocesso: {e}")

# Exemplo de uso:
camera_url = f"rtsp://{username}:{password}@{camera}:554/cam/realmonitor?channel=1&subtype=0"
movimento = Movimento(camera_url, largura=320, altura=240) # Define largura e altura menores
movimento.detectar_movimento() 