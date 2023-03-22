import hvac

class VaultKVClient:
    def __init__(self, vault_url: str, vault_token: str, mountpoint: str):
        self.client = hvac.Client()
        self.client.url = vault_url
        self.client.token = vault_token
        self.mountpoint = mountpoint
        
        assert self.client.is_authenticated()
    
    def list_secrets(self, path: str = ""):
        secretlist = self.client.secrets.kv.v2.list_secrets(mount_point=self.mountpoint, path=path)
        return secretlist.get('data', {}).get('keys', [])

    def read_secret(self, path: str):
        secret = self.client.secrets.kv.v2.read_secret(mount_point=self.mountpoint, path=path)
        return secret.get('data', {}).get('data', None)