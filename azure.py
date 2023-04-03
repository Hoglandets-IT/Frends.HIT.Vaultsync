from datetime import datetime
import os
from dataclasses import dataclass
import requests
import json


@dataclass
class AzureToken:
    """
    Token object for Azure authentication
    with caching functionality
    """

    token_type: str
    expires_in: int
    ext_expires_in: int
    expires_on: str
    not_before: str
    resource: str
    access_token: str
    cache_path: str = None

    def is_valid(self):
        """Check if the token is valid

        Returns:
            bool: Valid true/false
        """
        now = datetime.now().timestamp()

        print("checking validity")
        if self.access_token is None or self.expires_on is None:
            print("expires_at not set or token missing")
            return False

        if int(self.expires_on) < now:
            print("has expired")
            return False

        print("successfully authenticated")
        return True

    def save_cache(self):
        print("saving cache")
        try:
            with open(self.cache_path, "w") as f:
                json.dump(self.__dict__, f)

            print("cache saved")
        except Exception as e:
            print("cache save error")
            print("An error occured while saving Azure token cache: " + str(e))

    @classmethod
    def from_cache(
        cls,
        cache_path: str = None,
        request_on_fail: bool = False,
        request_tenant: str = None,
        request_azure_args: dict = None,
    ):
        """Get azure token from cache

        Args:
            cache_path (str, optional): Path to the cache file. Defaults to None.
            request_on_fail (bool, optional): Whether to request a new token if fetching the cache fails. Defaults to False.
            request_tenant (str, optional): The tenant for which to request the token. Defaults to None.
            request_azure_args (dict, optional): The arguments for fetching the token. Defaults to None.

        Returns:
            AzureToken: AzureToken instance
        """
        print("getting cache")
        if not cache_path or not os.path.isfile(cache_path):
            print("cache not found or path not set")
            if request_on_fail and request_tenant and request_azure_args:
                print("requesting new token")
                return cls.from_request(request_tenant, request_azure_args, cache_path)

            raise Exception("Azure token cache file not found: " + cache_path)

        with open(cache_path, "r") as f:
            print("checking cache")
            try:
                cache = json.load(f)
                print("cache loaded")
                cl = cls(**cache)
                assert cl.is_valid()
                return cl

            except Exception as e:
                if request_on_fail and request_tenant and request_azure_args:
                    print("requesting new token")
                    return cls.from_request(
                        request_tenant, request_azure_args, cache_path
                    )
                raise Exception("Azure token cache not valid: " + e)

    def get_key(self):
        return "?api_key" + self.token_type + " " + self.access_token

    def get_headers(self):
        return {
            "Authorization": " ".join((self.token_type, self.access_token)),
            "Accept": "application/json",
        }

    @classmethod
    def from_request(cls, tenant: str, azure_args: dict, cache_path: str = None):
        """Create a new instance by requesting a token from Azure

        Args:
            tenant (str): The Azure Tenant ID
            azure_args (dict): Arguments/credentials for the request
            cache_path (str, optional): The path to the cache file. Defaults to None.

        Returns:
            AzureToken: An instance of AzureToken
        """
        print("requesting new token")
        azure_args["grant_type"] = "client_credentials"
        azure_args["scope"] = azure_args["resource"]
        req = requests.post(
            "https://login.microsoftonline.com/"
            + tenant
            + ".onmicrosoft.com/oauth2/token",
            data=azure_args,
        )

        print("checking return status")
        if req.status_code != 200:
            raise Exception(
                "Authentication failed: " + str(req.status_code) + " " + req.text
            )

        print("creating token objects")
        token = req.json()

        if cache_path:
            print("saving token to cache")
            token["cache_path"] = cache_path
            cl = cls(**token)
            cl.save_cache()

        return cls(**token)
