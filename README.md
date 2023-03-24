# Vault to Frends Secret Synchronizer
Sync credentials and fields between Hashicorp Vault and Frends Integration Platform

## What is this?
This is a way to synchronize secrets from Hashicorp Vault to Frends, since the management of secrets is a bit more readable and manageable in Vault.

## Usage
### Configuration
```bash
# The name of the Azure tenant to query for authentication to the Frends Management API
AZURE_TENANT=""

# The Client ID used to authenticate (App Registration)
AZURE_CLIENT_ID=""

# The Client Secret used to authenticate (App Registration)
AZURE_CLIENT_SECRET=""

# The resource identifier to use for authentication
AZURE_RESOURCE=""

# If and where to store the Azure token cache between runs
AZURE_TOKEN_CACHE=""

# The HTTPS address to Hashicorp Vault
VAULT_ADDR=""

# The token used to authenticate to vault (needs to list and read secrets in the v2 KV store)
VAULT_TOKEN=""

# The name of the v2 KV store that contains the secrets
VAULT_STORE=""

# The base URL of the API to use (e.g. https://contoso.frendsapp.com/api/v0.9)
FRENDS_API_URL=""

# Debug mode will transfer all secrets from vault IN CLEAR TEXT to Frends
# After disabling this, all secrets created by this integration need to be deleted manually before 
# putting this into production
DEBUG_MODE=
```

### Vault Configuration
The key store on the Vault side needs to be a KV2 vault with namespacing enabled.
The following examples show secrets from Vault and their counterparts in Frends

```yaml
keys:  
    # Single-value secrets
  - vault: kv-store/SFTP/SERVER01/USERNAME
      content:
        value: "ThisIsAPassword"
    frends: "env.SFTP.SERVER01_USERNAME"
      content: |
        ThisIsAPassword

    # Multi-value secrets
  - vault: kv-store/SMB/SERVER01/USERNAME
      content:
        username: "username"
        password: "password"
    frends: "env.SFTP.SERVER01_USERNAME"
      content: |
        {
            "username": "username",
            "password": "password"
        }
  
```