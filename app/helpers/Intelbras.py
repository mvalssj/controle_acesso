import requests
import json
import base64
import json
from config import device_ip_in, device_ip_out, username, password

class UserAPI:
    def __init__(self, base_url_in, username, password):
        self.base_url_in = base_url_in
        self.auth = requests.auth.HTTPDigestAuth(username, password)

    def send_user(self, action, user_data):
        url = f"{self.base_url_in}?action={action}"
        response = requests.post(url, auth=self.auth, json=user_data)
        # print(response.status_code)
        # print(response.content)
        return response.status_code, response.content

class Usuarios:
    def __init__(self, url, username, password):
        self.url = url
        self.auth = requests.auth.HTTPDigestAuth(username, password)

    def obter_usuarios(self):
        response = requests.get(self.url, auth=self.auth)
        if response.status_code == 200:
            usuarios = self.parse_response(response.text)
            return usuarios
        else:
            print(f"Falha ao obter os usuários. Status code: {response.status_code}")
            return []

    def parse_response(self, response_text):
        usuarios = []
        lines = response_text.split('\n')
        usuario = {}
        for line in lines:
            if line.startswith('records['):
                key, value = line.split('=', 1)
                key = key.split('.', 1)[1]
                if key == 'CardName':
                    if usuario:
                        usuarios.append(usuario)
                    usuario = {}
                usuario[key] = value.strip()
        if usuario:
            usuarios.append(usuario)
        return [{"CardName": u["CardName"], "RecNo": u["RecNo"], "UserID": u["UserID"]} for u in usuarios]

    def obter_maior_userid(self, usuarios):
        if not usuarios:
            return None
        return max(usuarios, key=lambda u: int(u["UserID"]))
    
class BiometricRegistration:
    def __init__(self, device_ip_in, username, password):
        self.device_ip_in = device_ip_in
        self.username = username
        self.password = password
        self.url = f"http://{device_ip_in}/cgi-bin/AccessFace.cgi?action=insertMulti"
        self.auth = requests.auth.HTTPDigestAuth(username, password)
        self.headers = {'Content-Type': 'application/json'}

    def image_to_base64(self, image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def register_face(self, user_id, image_path):

        photo_base64 = self.image_to_base64(image_path)
        payload = json.dumps({
            "FaceList": [
                {
                    "UserID": user_id,
                    "PhotoData": [photo_base64]
                }
            ]
        })

        # print("Payload Biometria: ",payload)
        response = requests.post(self.url, auth=self.auth, headers=self.headers, data=payload)
        if response.text.strip() == "OK":
            print("Cadastro da face realizado com sucesso.")
        else:
            print("Erro ao cadastrar: " + response.text)

class Foto:
    def __init__(self, url, username, password):
        self.url = url
        self.auth = requests.auth.HTTPDigestAuth(username, password)

    def baixar_foto(self, caminho_arquivo):
        response = requests.get(self.url, auth=self.auth)
        if response.status_code == 200:
            with open(caminho_arquivo, "wb") as file:
                file.write(response.content)
            print(f"Foto salva como {caminho_arquivo}")
        else:
            print(f"Falha ao obter a foto. Status code: {response.status_code}")