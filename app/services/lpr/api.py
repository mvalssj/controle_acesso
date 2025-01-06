import time
from google.cloud import vision
import requests  # Importe a biblioteca requests no início do arquivo
import re
import io
import os
import segmentation as sg
import re, sys  # Adicione esta importação no início do seu arquivo main.py
import cv2
import pytesseract
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from config import lpr_offline

if lpr_offline == True:
    print("##### LPR Offline #####")
else:
    print("##### LPR Google Vision #####")
# Verifica se o número de argumentos é correto (deve ser 3: o script, foto_placa e file_placa)
if len(sys.argv) > 1:
    foto_placa = sys.argv[1]
    # print(foto_placa)
    file_placa = sys.argv[2]
    # print(file_placa)
else:
    foto_placa = "live.jpg"
    file_placa = "placa_frontal.txt"

# print(file_placa)    

os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="app\\services\\lpr\\Credenciais\\tonal-depth-255918-b8558635b39f.json"
TEXTS=[]

# Envia reconhece a placa offiline
def reconhecer_placa_offline(caminho_imagem):
    try:
        print("########## Reconhecendo placa ##########")
        imagem = cv2.imread(caminho_imagem)
        # Converta para escala de cinza se a imagem não for colorida
        if len(imagem.shape) == 3:
            imagem = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)

        # Pré-processamento da imagem (aprimorado)
        imagem = cv2.resize(imagem, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        # Adicionando filtro bilateral para reduzir ruído preservando bordas
        imagem = cv2.bilateralFilter(imagem, 9, 75, 75)
        imagem = cv2.GaussianBlur(imagem, (5, 5), 0)
        _, imagem = cv2.threshold(imagem, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Melhorando a segmentação usando morfologia matemática
        kernel = np.ones((5,5),np.uint8)
        imagem = cv2.morphologyEx(imagem, cv2.MORPH_OPEN, kernel) #Remove pequenos ruídos
        imagem = cv2.morphologyEx(imagem, cv2.MORPH_CLOSE, kernel) #Fecha buracos

        # Configuração do Tesseract (aprimorada)
        # Testando diferentes PSMs e adicionando --oem 3 para melhor desempenho
        for psm in range(3, 14):  # Testando PSMs de 3 a 13
            config = f'--psm {psm} --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
            texto = pytesseract.image_to_string(imagem, lang='por', config=config)
            print(f"Testando com PSM {psm}: {texto}")

            # Padrões de placas Mercosul e antigo (XXX-XXXX e XXXXXXX)
            padrao_mercosul = r"[A-Z]{3}[0-9]{1}[A-Z]{1}[0-9]{2}"
            padrao_antigo = r"[A-Z]{3}[0-9]{4}"

            # Busca por um dos padrões
            match_mercosul = re.search(padrao_mercosul, texto)
            match_antigo = re.search(padrao_antigo, texto)

            if match_mercosul or match_antigo:
                texto_placa = match_mercosul.group(0) if match_mercosul else match_antigo.group(0)
                return texto_placa

        return None

    except Exception as e:
        print(f"Erro ao processar a imagem: {e}")
        return None

# Envia a placa via webhook 
def send_plate_data(plate_number):
    url = 'http://192.168.10.35:93/relatorios/simula_balanca/integracao.php'
    data = {'plate_number': plate_number}
    headers = {'Content-Type': 'application/json'}  # Definindo o tipo de conteúdo como JSON
    
    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()  # Lança uma exceção se houver um erro na resposta
        print(f'Successfully sent plate number: {plate_number}')
    except requests.exceptions.RequestException as err:
        print(f'Error sending plate number: {err}')

# Instantiates Aciona a api do google
def detect_text(path):
    """Detects text in the file."""
    print('Enviando para a Google Vision...')
    client = vision.ImageAnnotatorClient()
    with io.open(path, 'rb') as image_file:
        content = image_file.read()
    image = vision.Image(content=content)

    response = client.text_detection(image=image)
    # print('Aguarde 10 segundos para enviar novamente...')
    # time.sleep(10)    
    texts = response.text_annotations
   # print('Texts:')

    for text in texts:
        #print('\n"{}"'.format(text.description))
        dict={'description': text.description, 'Locale':text.locale, 'Vertices':text.bounding_poly.vertices}
        TEXTS.append(dict)
        vertices = (['({},{})'.format(vertex.x, vertex.y)
                    for vertex in text.bounding_poly.vertices])

        #print('bounds: {}'.format(','.join(vertices)))

    if response.error.message:
        raise Exception(
            '{}\nFor more info on error messages, check: '
            'https://cloud.google.com/apis/design/errors'.format(
                response.error.message))

crop_path=sg.preprocessing(f'app\\services\\lpr\\images\\{foto_placa}')
print('Cortou imagem da placa')
# Mudança proposta no código principal
if crop_path is not None:


    if lpr_offline == True: 
        print("### Execução Offiline ###")
        full_placa = reconhecer_placa_offline(crop_path)
        condicao = full_placa
    else:
        print("### Execução Google Vision ###")
        detect_text(crop_path) # usar api do google
        full_placa = TEXTS[0]['description']
        condicao = TEXTS   

    # detect_text(crop_path) # usar api do google
        
    # full_placa = reconhecer_placa_offline(crop_path)

    # if TEXTS:  # Verifica se a lista TEXTS não está vazia  # usar api do google
    print("######## Texto detectado:", full_placa)
    if condicao:
        # full_text = TEXTS[0]['description']  # usar api do google       
        full_text = full_placa
        # Use uma expressão regular para manter apenas letras e números
        clean_text = re.sub(r'[^A-Za-z0-9]', '', full_text)

        # Verifica se o texto limpo segue o padrão de 3 letras seguidas por 4 números
        if re.match(r'^[A-Za-z]{3}\d{4}$', clean_text) or re.match(r'^[A-Za-z]{3}\d{1}[A-Za-z]{1}\d{2}$', clean_text):
            print("Padrão de placa válido detectado.")
            placa = format(clean_text[-7:])
            with open(os.path.join(f'app\\services\\lpr\\{file_placa}'), 'w') as f:  # Abre o arquivo 'placa.txt' para escrita na mesma pasta do arquivo api.py
                f.write(placa)  # Escreve o valor de 'placa' no arquivo
        else:
            print("Padrão de placa inválido.")
            with open(os.path.join(f'app\\services\\lpr\\{file_placa}'), 'w') as f:  # Abre o arquivo 'placa.txt' para escrita na mesma pasta do arquivo api.py
                f.write('Fora do Padrão')  # Escreve o valor de 'placa' no arquivo
    
        # Enviando a placa detectada para o servidor
        # send_plate_data(clean_text[-7:])    
        print("Placa: {}".format(clean_text[-7:]))
        # time.sleep(30)  # Aguarda 30 segundos
    else:
        print('Nenhum texto detectado na imagem.')
        with open(os.path.join(f'app\\services\\lpr\\{file_placa}'), 'w') as f:  # Abre o arquivo 'placa.txt' para escrita na mesma pasta do arquivo api.py
            f.write('Não Detectado.')  # Escreve o valor de 'placa' no arquivo

else:
    print('Tente outra imagem!')
    with open(os.path.join(f'app\\services\\lpr\\{file_placa}'), 'w') as f:  # Abre o arquivo 'placa.txt' para escrita na mesma pasta do arquivo api.py
        f.write('Não Detectado.')  #Escreve o valor de 'placa' no arquivo
