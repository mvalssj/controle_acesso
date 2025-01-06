from PIL import Image
import pytesseract
import sys
import os
# Obtém o caminho absoluto do diretório do script atual
dir_atual = os.path.dirname(os.path.abspath(__file__))
# Obtém o caminho absoluto do diretório três níveis acima
dir_raiz = os.path.dirname(os.path.dirname(os.path.dirname(dir_atual)))

# Adiciona o diretório raiz ao caminho de busca do Python
if dir_raiz not in sys.path:
    sys.path.insert(0, dir_raiz)

import config

# Verifica se o número de argumentos é correto (deve ser 3: o script, foto_placa e file_placa)
if len(sys.argv) > 1:
    foto_placa = sys.argv[1]
    print('Foto Placa: ',foto_placa)
    file_placa = sys.argv[2]
    print('File Placa: ', file_placa)

if foto_placa == "placa_frontal.jpg":
    imagem_path = 'app\\services\\lpr\\images\\string_frontal.jpg'  # Substitua pelo caminho da sua imagem
elif foto_placa == "placa_traseira.jpg":
    imagem_path = 'app\\services\\lpr\\images\\string_traseira.jpg'  # Substitua pelo caminho da sua imagem
else:
    imagem_path = 'app\\services\\lpr\\images\\string_entrada.jpg'  # Substitua pelo caminho da sua imagem

# Carregar a imagem
imagem = Image.open(imagem_path)

padrao_antigo = r'^[A-Z]{3}\-\d{4}$'  # Ex: ABC-1234
padrao_novo = r'^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$' # Ex: ABC1D23
padrao_sem_hifen = r'^[A-Z]{3}\d{4}$' #Adicionado: padrão sem hífen

# Usar o Tesseract para extrair o texto da imagem

texto = pytesseract.image_to_string(imagem, config='--psm 6 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', lang='por')

placa = texto.strip().upper() # converte para maiúsculo para comparação
placa_7_caracteres = placa[:7] # Fatiamento para pegar os 7 primeiros caracteres

print('7 Primeiros caracteres: ',placa_7_caracteres)

# Verifica se a placa corresponde a algum padrão
if placa_7_caracteres != "SP7": #Alteração: inclusão do novo padrão na verificação

# if re.match(padrao_antigo, placa_7_caracteres) or re.match(padrao_novo, placa_7_caracteres) or re.match(padrao_sem_hifen, placa_7_caracteres): #Alteração: inclusão do novo padrão na verificação
    # Grava o texto extraído no arquivo especificado na variável file_placa
    
    output_path = f'app\\services\\lpr\\{file_placa}'  # Correção aqui
    with open(output_path, 'w', encoding='utf-8') as file:  
        file.write(placa_7_caracteres)
else:
    output_path = f'app\\services\\lpr\\{file_placa}'  # Correção aqui
    print('#### Output Path ####',output_path)
    with open(output_path, 'w', encoding='utf-8') as file:
        file.write("--")

print("Texto extraído:", placa)