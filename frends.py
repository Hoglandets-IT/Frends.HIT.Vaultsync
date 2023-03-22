import requests
import json
from azure import AzureToken

class FrendsClient:
    def __init__(self, url: str, token: AzureToken):
        self.url = url
        self.token = token
        self.headers = {
            # 'Authorization': token.get_header(),
            'Content-Type':  'application/json'
        }

    def list_env(self):
        print("Requesting url " + self.url + '/environment-variables')
        req = requests.get('https://hoglandet.frendsapp.com/api/v0.9/environment-variables?api_key='+self.token.access_token, headers=self.headers)
        
        if req.status_code == 200:
            res = req.json()
            return res

        print("Hold")