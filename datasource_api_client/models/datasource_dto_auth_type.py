from enum import Enum


class DatasourceDtoAuthType(str, Enum):
    AZUREBASIC = "AzureBasic"
    BASIC = "Basic"
    AWSIAMBASIC = "AWSIAMBasic"
    AWSIAMROLE = "AWSIAMRole"
    GCPBASIC = "GCPBasic"
    OAUTH = "OAuth"

    def __str__(self) -> str:
        return str(self.value)
