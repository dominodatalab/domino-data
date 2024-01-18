from enum import Enum


class DatasourceDtoAuthType(str, Enum):
    AZUREBASIC = "AzureBasic"
    BASIC = "Basic"
    AWSIAMBASIC = "AWSIAMBasic"
    AWSIAMBASICNOOVERRIDE = "AWSIAMBasicNoOverride"
    AWSIAMROLE = "AWSIAMRole"
    AWSIAMROLEWITHUSERNAME = "AWSIAMRoleWithUsername"
    GCPBASIC = "GCPBasic"
    OAUTH = "OAuth"
    OAUTHTOKEN = "OAuthToken"
    CLIENTIDSECRET = "ClientIdSecret"
    PERSONALTOKEN = "PersonalToken"

    def __str__(self) -> str:
        return str(self.value)
