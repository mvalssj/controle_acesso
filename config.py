# config.py
unidade = 5 #TMG
TIMEZONE = 'America/Sao_Paulo'
device_ip_in = '192.168.9.11'
device_ip_out = '192.168.9.12'
device_ip_in_truck = '192.168.10.63'
device_ip_in_car = '192.168.10.63'
device_ip_out_truck = '192.168.10.63'
device_ip_out_car = '192.168.10.63'

device_ip_lpr_entrada = '10.25.248.60'
device_ip_lpr_frente = '192.168.9.13'
device_ip_lpr_fundo = '192.168.9.14'

camera_entrada_pedestre = "rtsp://admin:Inter2574@10.25.248.60:554/cam/realmonitor?channel=1&subtype=0"
camera_placa_frontal_balanca = "rtsp://admin:Inter2574@192.168.9.14:554/cam/realmonitor?channel=1&subtype=0"
camera_placa_traseira_balanca = "rtsp://admin:Inter2574@192.168.9.13:554/cam/realmonitor?channel=1&subtype=0"
username = 'admin'
password = 'Inter2574'
base_url_in = f"http://{device_ip_in}/cgi-bin/AccessUser.cgi"
base_url_out = f"http://{device_ip_out}/cgi-bin/AccessUser.cgi"
path_foto = 'app\\static\\images'
catraca = "64b021f0-1fd2-46ee-8962-43c2e66e5035"
siscomex = "https://isopeteste.intermaritima.com.br/res/api/acesso_pessoas.php"
lpr_offline = True

class Config:
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:cablev35@192.168.0.15:3307/controle_acesso'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'Krrjb39142114@@@#'

    # Adicione as variáveis do arquivo config.py como atributos da classe Config
    TIMEZONE = TIMEZONE
    device_ip_in = device_ip_in
    device_ip_out = device_ip_out
    device_ip_in_truck = device_ip_in_truck
    device_ip_in_car = device_ip_in_car
    device_ip_out_truck = device_ip_out_truck
    device_ip_out_car = device_ip_out_car

    device_ip_lpr_frente = device_ip_lpr_frente
    device_ip_lpr_fundo = device_ip_lpr_fundo

    camera_entrada_pedestre = camera_entrada_pedestre
    camera_placa_frontal_balanca = camera_placa_frontal_balanca
    camera_placa_traseira_balanca  = camera_placa_traseira_balanca
    username = username
    password = password
    base_url_in = base_url_in
    base_url_out = base_url_out
    path_foto = path_foto
    catraca = catraca
    siscomex = siscomex
    lpr_offline = lpr_offline
    unidade = unidade
