import requests
import json
import re
from datetime import datetime
from dotenv import load_dotenv
import os
from azure import AzureToken
from frends import FrendsClient
from vault import VaultKVClient


load_dotenv()

def fmt_str(string: str):
    # Identify all characters except for letters, numbers and underscore
    rgx = re.compile(r"[^a-zA-Z0-9_]")
    
    # Return uppercase name special characters replaced by underscore
    return rgx.sub("_", string).upper()

class Sync:
    frends_url: str
    vault_address: str
    vault_token: str
    
    azure_tenant: str
    azure_auth: dict
    azure_token_cache: str = None
        
    azure_token: AzureToken = None
    frends_client: FrendsClient = None
    vault_client: VaultKVClient = None
    

    @staticmethod
    def env_var(env: str, required: bool = False):
        va = os.getenv(env)
        
        if required and va is None:
            raise Exception("Missing required environment variable: " + env)

        return va
    
    def __init__(self):
        self.azure_auth = {
            "client_id": self.env_var('AZURE_CLIENT_ID', True),
            "client_secret": self.env_var('AZURE_CLIENT_SECRET', True),
            "resource": self.env_var('AZURE_RESOURCE', True)
        }

        self.azure_tenant = self.env_var('AZURE_TENANT', True)
        self.azure_token_cache = self.env_var('AZURE_TOKEN_CACHE', False)
        
        self.vault_address = self.env_var('VAULT_ADDR', True)
        self.vault_token = self.env_var('VAULT_TOKEN', True)
        self.vault_store = self.env_var('VAULT_STORE', True)
        
        self.frends_url = self.env_var('FRENDS_API_URL', True)
        
    def login(self):
        self.azure_token = AzureToken.from_cache(
            self.azure_token_cache,
            True,
            self.azure_tenant,
            self.azure_auth
        )
        
        self.vault_client = VaultKVClient(
            self.vault_address,
            self.vault_token,
            self.vault_store
        )
        
        self.frends_client = FrendsClient(self.frends_url, self.azure_token)

if __name__ == '__main__':
    sync = Sync()
    sync.login()
    print(sync.frends_client.list_env())
    print("Hold")

# client = hvac.Client()
# client.token = config.vault_token
# client.url = config.vault_address

# assert client.is_authenticated()

# token = None

# if config.azure_token_cache and config.azure_token_cache != "":
#     if not os.path.isfile(config.azure_token_cache):
#         with open(config.azure_token_cache, 'w') as f:
#             f.write('{}')

#     with open(config.azure_token_cache, 'r') as f:
#         token = json.load(f)

# if not isinstance(token, dict) or token.get('expires_at', 0) < datetime.now().timestamp():
#     tenant = config.azure_tenant
#     azauth = {
#         "client_id": config.azure_client_id,
#         "audience": config.azure_audience,
#         "scope": "https://graph.microsoft.com/.default",
#         "client_secret": config.azure_client_secret,
#         "grant_type": "client_credentials"
#     }
#     token_req = requests.post("https://login.microsoftonline.com/" + tenant + ".onmicrosoft.com/oauth2/v2.0/token", data = azauth)
    
#     if token_req.status_code == 200:
#         token = token_req.json()
#         token['expires_at'] = int(datetime.now().timestamp() + token_req.json()['expires_in'])

# if os.path.isfile(config.azure_token_cache):
#     with open(config.azure_token_cache, 'w') as f:
#         json.dump(token, f)

# frurl = "https://hoglandet.frendsapp.com/api/v1/"

# secret_list = {}

# # Get a list of secrets from vault
# types = client.secrets.kv.v2.list_secrets(mount_point=config.vault_store, path="")

# for credtype in types['data']['keys']:
#     servers = client.secrets.kv.v2.list_secrets(mount_point=config.vault_store, path=credtype)
#     secret_list[fmt_str(credtype)] = secret_list.get(fmt_str(credtype), {})
    
#     for server in servers['data']['keys']:
#         accounts = client.secrets.kv.v2.list_secrets(mount_point=config.vault_store, path=os.path.join(credtype, server))
        
#         for account in accounts['data']['keys']:
#             content = client.secrets.kv.v2.read_secret(mount_point=config.vault_store, path=''.join((credtype, server, account)))
            
#             fr_accountname = account
#             fr_content = content.get('data', {}).get('data', None)
            
#             if isinstance(fr_content, dict) and fr_content.get('connectiontype', False):
#                 if fr_content.get('domain', False):
#                     fr_accountname = f"{fr_content['domain']}_{fr_accountname}"
#                 fr_content['password'] = ""
#                 secret_list[fmt_str(credtype)][fmt_str(''.join((server, fr_accountname)))] = content['data']['data']
