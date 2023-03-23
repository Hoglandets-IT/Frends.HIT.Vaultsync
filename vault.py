import hvac, re, os

def fmt_str(string: str):
    # Identify all characters except for letters, numbers and underscore
    rgx = re.compile(r"[^a-zA-Z0-9_]")
    
    # Return uppercase name special characters replaced by underscore
    return rgx.sub("_", string).upper().rstrip("_")

class VaultKVClient:
    def __init__(self, vault_url: str, vault_token: str, mountpoint: str):
        self.client = hvac.Client()
        self.client.url = vault_url
        self.client.token = vault_token
        self.mountpoint = mountpoint
        
        assert self.client.is_authenticated()
    
    def list_secrets(self, path: str = ""):
        try:
            secretlist = self.client.secrets.kv.v2.list_secrets(mount_point=self.mountpoint, path=path)
        except hvac.exceptions.InvalidPath:
            secretlist = {}

        return secretlist.get('data', {}).get('keys', [])
    
    def list_secrets_recursive(self, path: str = ""):
        secret_tree = self.list_secrets(path)
        out = {}
        if len(secret_tree) > 0:
            for value in secret_tree:
                newpath = os.path.join(path, value)
                out[fmt_str(value)] = self.list_secrets_recursive(newpath)
        else:
            try:
                return self.read_secret(path)
            except hvac.exceptions.InvalidPath:
                newpath = '/'.join(newpath.split('/')[0:-1])
                return self.read_secret(newpath)
        return out
        print("Hold")

    def read_secret(self, path: str):
        secret = self.client.secrets.kv.v2.read_secret(mount_point=self.mountpoint, path=path)
        return secret.get('data', {}).get('data', None)