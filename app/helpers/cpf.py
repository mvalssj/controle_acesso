import requests
 
device_ip = '192.168.10.62'
username = 'admin'
password = 'Inter2574'
 
CardList = (
 
        '''{
                "CardList": [
                    {
                        "UserID": "1",
                        "CardNo": "03457462526",
                        "CardType": "0"  ,
                        "CardStatus": "0"
                    }
                ]
            }''' )
 
url = "http://{}/cgi-bin/AccessCard.cgi?action=insertMulti".format(
                        str(device_ip),
                    )
 
digest_auth = requests.auth.HTTPDigestAuth(username, password)
rval = requests.get(url, data=CardList, auth=digest_auth, stream=True, timeout=20, verify=False)
 
print(rval.text)