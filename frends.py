import requests
import json
from datetime import datetime
from azure import AzureToken
from dataclasses import dataclass
from dataclasses_json import dataclass_json
from enum import Enum
from typing import List

FUNCTION_TYPE = type(print)


@dataclass_json
@dataclass
class FrendsEnvironmentBase:
    """Class for marshalling/unmarshalling a json object"""

    id: int
    displayName: str


@dataclass_json
@dataclass
class FrendsEnvironmentVariableValue:
    """Class for marshalling/unmarshalling a json object"""

    environment: FrendsEnvironmentBase
    value: str
    modifiedUtc: str = None
    modifier: str = None
    version: int = None


@dataclass_json
@dataclass
class FrendsEnvironmentVariable:
    """Class for marshalling/unmarshalling a json object"""

    id: int
    name: str
    type: str
    description: str = None
    valuesJson: str = None
    childSchemasJson: str = None
    values: List[FrendsEnvironmentVariableValue] = None
    childSchemas: List["FrendsEnvironmentVariable"] = None

    def __post_init__(self):
        if self.childSchemasJson is not None:
            self.childSchemas = []

            for item in self.childSchemasJson:
                item["valuesJson"] = item.pop("values")

                self.childSchemas.append(
                    FrendsEnvironmentVariable.from_json(json.dumps(item))
                )

        if self.valuesJson is not None:
            self.values = [
                FrendsEnvironmentVariableValue.from_json(json.dumps(x))
                for x in self.valuesJson
            ]

    def __str__(self):
        return f"{self.__class__.__name__}({self.name}))"

    def __repr__(self):
        return repr(self.__str__())


class FrendsClient:
    """
    The client used to send requests to Frends
    """

    def __init__(self, url: str, token: AzureToken):
        self.url = url
        self.token = token

        self.environments = []
        self.get_agentgroups()

    def request(
        self,
        path: str,
        method: FUNCTION_TYPE = requests.get,
        args=None,
        argtype: str = "json",
    ):
        """Make a request to the Frends API

        Args:
            path (str): resource path
            method (FUNCTION_TYPE, optional): The request method to use. Defaults to requests.get.
            args (dict, optional): Arguments to include with the request. Defaults to None.
            argtype (str, optional): Type of arguments. Defaults to 'json'.

        Returns:
            dict: Resulting dictionary from the request
        """
        print("Requesting url " + self.url + path)
        common = {
            "url": f"{self.url}{path}",
            "headers": self.token.get_headers(),
        }
        if method == requests.get:
            common["params"] = args
        elif argtype == "json":
            common["json"] = args
        elif argtype == "plain":
            common["headers"]["Content-Type"] = "text/plain"
            common["data"] = args
        else:
            common["data"] = args

        req = method(**common)
        if req.status_code < 300:
            try:
                return req.json()
            except:
                return req.text

        raise Exception("An error occured", req.status_code, req.text)

    def get_agentgroups(self):
        """Get all agent groups from Frends"""
        req = self.request("/environments", requests.get)
        for envi in req["data"]:
            if envi["id"] not in self.environments:
                self.environments.append(envi["id"])

    def set_env_description(self, id: str, description: str):
        """Set the description of the environment variable/group

        Args:
            id (str): The identifier of the variable/group
            description (str): The description to set
        """
        if description is not None:
            self.request(
                f"/environment-variables/{id}",
                requests.patch,
                {"description": description},
            )

    def create_env_group(self, name: str):
        """Create an environment variable group

        Args:
            name (str): Name of the group

        Returns:
            dict: The group data
        """
        print("Creating environment group...")

        reval = self.request("/environment-variables", requests.post, {"name": name})

        return reval.get("data", None)

    def get_env(self, name: str):
        """Fetches an environment variable from Frends

        Args:
            name (str): The name of the environment variable

        Returns:
            FrendsEnvironmentVariable: An environment variable object
        """
        print("Fetching variable...")
        req = requests.get(
            f"{self.url}/environment-variables?environmentVariableName={name}",
            headers=self.token.get_headers(),
        )

        if req.status_code == 200:
            res = req.json()
            if len(res["data"]) > 0:
                return FrendsEnvironmentVariable.from_json(json.dumps(res["data"][0]))
            return None

        raise Exception("Error occured", req.status_code, req.text)

    def insert_update_env(
        self,
        parent: int,
        name: str,
        content: str,
        only_env: list = None,
        var_type: str = "Secret",
    ):
        """Insert or update an environment variable

        Args:
            parent (int): The parent group ID
            name (str): Name of the environment variable
            content (str): Content of the variable
            only_env (list, optional): include only certain environment variables. Defaults to None.
            var_type (str, optional): Type of variable. Defaults to "Secret".
        """
        check = self.get_env(name)

        # Create if not present
        if check is None:
            self.request(
                f"/environment-variables/{parent}",
                requests.post,
                {
                    "type": var_type,
                    "name": name,
                },
            )
            check = self.get_env(name)

        # Set the values
        value_envs = self.environments if only_env is None else only_env

        if not [x.value for x in check.values] == [content] * len(check.values):
            for env in value_envs:
                try:
                    self.request(
                        f"/environment-variables/{check.id}/values/{env}",
                        requests.put,
                        content,
                    )
                except Exception as e:
                    # Workaround for API bug where no values can be updated
                    # if the env var does not exist for that environment
                    print(
                        "Setting environment value for environment failed, trying the workaround...."
                    )
                    resp = requests.post(
                        f'{self.url.replace("v0.9", "environmentVariable")}/updateEnvironmentVariables',
                        headers=self.token.get_headers(),
                        json=[
                            {
                                "environmentId": env,
                                "newValue": content,
                                "schemaId": check.id,
                                "version": 1,
                            }
                        ],
                    )

                    if resp.status_code > 200:
                        raise Exception(
                            "Workaround failed as well", resp.status_code, resp.text
                        )

    def list_env(self, page_number: int = 1, page_size: int = 200):
        """List environment variables

        Args:
            page_number (int, optional): The page number. Defaults to 1.
            page_size (int, optional): Size of the page. Defaults to 200.

        Returns:
            List[FrendsEnvironmentVariable]: List of variables
        """
        print("Listing environment variables")
        response = self.request(
            "/environment-variables",
            requests.get,
            {"pagingQuery.pageNumber": page_number, "pagingQuery.pageSize": page_size},
        )

        envvars = {}

        for envv in response["data"]:
            if len(envv["childSchemas"]) > 0:
                envv["childSchemasJson"] = envv.pop("childSchemas")
                envv["valuesJson"] = envv.pop("values")

                envvar = FrendsEnvironmentVariable.from_json(json.dumps(envv))
                envvars[envvar.name] = envvar

        return envvars
