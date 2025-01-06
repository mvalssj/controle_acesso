import requests

# URL para obter a lista de pessoas
url_pessoas = "http://192.168.0.40:85/api/v1/colaboradores"

# URL da API de cadastro
api_cadastro_url = "http://127.0.0.1/api/cadastrar"

# Dados fixos a serem enviados com cada pessoa
fixed_data = {
    "password": "142114",
    "doors": [0],
    "time_sections": [2],
    "valid_from": "2024-03-10T10:00:00",
    "valid_to": "2040-03-10T10:00:00",
    "foto": ""
}

# Fazendo a requisição GET para obter a lista de pessoas
response = requests.get(url_pessoas)

# Verificando se a requisição foi bem-sucedida
if response.status_code == 200:
    # Carregando a lista de pessoas
    pessoas = response.json()
    
    # Percorrendo cada pessoa e enviando o JSON correspondente
    for pessoa in pessoas:
        # Criando o JSON para enviar para a API de cadastro
        payload = {
            "username": pessoa['nome'],
            "cpf": pessoa['cpf']
        }
        
        # Adicionando os dados fixos ao payload
        payload.update(fixed_data)
        
        # Enviando o request para a API de cadastro
        cadastro_response = requests.post(api_cadastro_url, json=payload)
        
        # Verificando o status da resposta
        if cadastro_response.status_code == 200:
            print(f"Usuário {pessoa['nome']} cadastrado com sucesso.")
        else:
            print(f"Erro ao cadastrar usuário {pessoa['nome']}: {cadastro_response.status_code} - {cadastro_response.text}")
else:
    print(f"Erro ao obter a lista de pessoas: {response.status_code} - {response.text}")
