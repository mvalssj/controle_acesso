import requests
import re
 
device_ip = '192.168.9.11'
username = 'admin'
password = 'Inter2574'  
# verifica se o já está na controladora

cpf = '03457462522'
url = f"http://{device_ip}/cgi-bin/AccessCard.cgi?action=list&CardNoList[0]={cpf}"

digest_auth = requests.auth.HTTPDigestAuth(username, password)
rval = requests.get(url, auth=digest_auth, stream=True, timeout=20, verify=False)
# print('############# Cadastro cpf:',rval.text)

user_id = None
match = re.search(r'UserID=(\d+)', rval.text)
if match:
    user_id = match.group(1)

print('UserID:', user_id)

# verifica se o já está na controladora