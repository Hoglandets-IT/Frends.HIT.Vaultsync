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


class Sync:
    """Container class for the sync process"""

    frends_url: str
    vault_address: str
    vault_token: str

    azure_tenant: str
    azure_auth: dict
    azure_token_cache: str = None

    azure_token: AzureToken = None
    frends_client: FrendsClient = None
    vault_client: VaultKVClient = None

    debug_mode: bool = False

    @staticmethod
    def env_var(env: str, required: bool = False):
        """Get a variable from environment or fail

        Args:
            env (str): Name of the environment variable
            required (bool, optional): Whether the variable is required. Defaults to False.

        Raises:
            Exception: The variable was not found

        Returns:
            str: The environment variable value
        """
        va = os.getenv(env)

        if required and va is None:
            raise Exception("Missing required environment variable: " + env)

        return va

    def __init__(self):
        self.azure_auth = {
            "client_id": self.env_var("AZURE_CLIENT_ID", True),
            "client_secret": self.env_var("AZURE_CLIENT_SECRET", True),
            "resource": self.env_var("AZURE_RESOURCE", True),
        }

        self.azure_tenant = self.env_var("AZURE_TENANT", True)
        self.azure_token_cache = self.env_var("AZURE_TOKEN_CACHE", False)

        self.vault_address = self.env_var("VAULT_ADDR", True)
        self.vault_token = self.env_var("VAULT_TOKEN", True)
        self.vault_store = self.env_var("VAULT_STORE", True)

        self.frends_url = self.env_var("FRENDS_API_URL", True)

        if isinstance(self.env_var("DEBUG_MODE", False), str) and self.env_var(
            "DEBUG_MODE", False
        ).lower() in ["true", "1", "yes"]:
            print("\033[31m!!!! WARNING: Debug mode is enabled !!!!")
            print("All secrets WILL BE TRANSFERRED IN CLEAR TEXT FORM")
            print(
                "After disabling debug mode, all secrets need to be deleted and re-synced\033[0m"
            )

            self.debug_mode = True

    def login(self):
        """Log in to Azure and Vault"""
        self.azure_token = AzureToken.from_cache(
            self.azure_token_cache, True, self.azure_tenant, self.azure_auth
        )

        self.vault_client = VaultKVClient(
            self.vault_address, self.vault_token, self.vault_store
        )

        self.frends_client = FrendsClient(self.frends_url, self.azure_token)

    def flatten_tree(self, namespaced: dict):
        """Flatten the hierarchical Vault KV store to a flat dictionary

        Args:
            namespaced (dict): The hierarchical dictionary from vault

        Returns:
            dict: 2-level list of key, value pairs
        """
        flat = {}
        for key, value in namespaced.items():
            if any([isinstance(child, dict) for child in value.values()]):
                flat = {
                    **flat,
                    **{
                        f"{key}_{subkey}": value
                        for subkey, value in self.flatten_tree(value).items()
                    },
                }
            else:
                flat[key] = value

        return flat

    def namespaced_to_flat_json(self, namespaced: dict):
        """Convert to flat dict with the last item formatted as json string

        Args:
            namespaced (dict): The hierarchical dictionary from vault

        Returns:
            dict: 2-level dict
        """
        top_level = namespaced.keys()
        flat = {}
        for variable in top_level:
            flat[variable] = {
                key: json.dumps(value)
                for key, value in self.flatten_tree(namespaced[variable]).items()
            }

        return flat

    def update_frends(self, vault: dict):
        """Update the environment variables in Frends

        Args:
            vault (dict): The formatted values from Hashicorp Vault
        """
        for toplevel, items in vault.items():
            frends = self.frends_client.get_env(toplevel)

            if frends is None:
                envid = self.frends_client.create_env_group(toplevel)
            try:
                self.frends_client.set_env_description(
                    getattr(frends, "id", None) or envid,
                    "Automatically synced from Vault",
                )
            except Exception:
                pass

            for key, value in items.items():
                # Check if there are multiple fields in the json or just one
                fields = json.loads(value)
                if len(fields) == 1 and isinstance(fields, dict):
                    value = fields[list(fields.keys())[0]]

                var_type = "Secret"

                if self.debug_mode is True:
                    print("\033[31m!!!! WARNING: Debug mode is enabled !!!!")
                    print("All secrets WILL BE TRANSFERRED IN CLEAR TEXT FORM")
                    print(
                        "After disabling debug mode, all secrets need to be deleted and re-synced\033[0m"
                    )

                    var_type = "String"

                self.frends_client.insert_update_env(
                    parent=getattr(frends, "id", None) or envid,
                    name=key,
                    content=value,
                    var_type=var_type,
                )


if __name__ == "__main__":
    sync = Sync()
    sync.login()

    # Retrieve namespaced recursive list of secrets in the Vault KV store
    namespaced = sync.vault_client.list_secrets_recursive()

    # Flatten the namespaces to turn SMB/SERVER/ACCOUNT into SMB.SERVER_ACCOUNT
    flat = sync.namespaced_to_flat_json(namespaced)
    sync.update_frends(flat)

    print("Finished!")
