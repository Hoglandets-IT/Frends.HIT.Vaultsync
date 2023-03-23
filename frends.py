import requests
import json
from datetime import datetime
from azure import AzureToken
from dataclasses import dataclass
from dataclasses_json import dataclass_json
from enum import Enum
from typing import List

@dataclass_json
@dataclass
class FrendsEnvironmentBase:
    id: int
    displayName: str

@dataclass_json
@dataclass
class FrendsEnvironmentVariableValue:
    environment: FrendsEnvironmentBase
    value: str
    modifiedUtc: str = None
    modifier: str = None
    version: int = None

@dataclass_json
@dataclass
class FrendsEnvironmentVariable:
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
                item['valuesJson'] = item.pop('values')
                
                self.childSchemas.append(FrendsEnvironmentVariable.from_json(json.dumps(item)))
                
        if self.valuesJson is not None:
            self.values = [FrendsEnvironmentVariableValue.from_json(json.dumps(x)) for x in self.valuesJson]
        

    def __str__(self):
        return f"{self.__class__.__name__}({self.name}))"
    
    def __repr__(self):
        return repr(self.__str__())

class FrendsClient:
    def __init__(self, url: str, token: AzureToken):
        self.url = url
        self.token = token

    def list_env(self, page_number: int = 1, page_size: int = 200):
        print("Requesting url " + self.url + '/environment-variables')
        req = requests.get(f'{self.url}/environment-variables?pagingQuery.pageNumber={page_number}&pagingQuery.pageSize={page_size}', headers=self.token.get_headers())
        
        if req.status_code == 200:
            res = req.json()
            envvars = {}
            
            for envv in res['data']:
                if len(envv['childSchemas']) > 0:
                    envv['childSchemasJson'] = envv.pop('childSchemas')
                    envv['valuesJson'] = envv.pop('values')

                    envvar = FrendsEnvironmentVariable.from_json(json.dumps(envv))
                    envvars[envvar.name] = envvar
                
            return envvars
        raise Exception("An error occured")

        print("Hold")