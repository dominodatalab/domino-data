from enum import Enum


class DatasourceDtoAuthType(str, Enum):
    AWSIAMBASIC = "AWSIAMBasic"
    AWSIAMBASICNOOVERRIDE = "AWSIAMBasicNoOverride"
    AWSIAMROLE = "AWSIAMRole"
    AWSIAMROLEWITHUSERNAME = "AWSIAMRoleWithUsername"
    AZUREBASIC = "AzureBasic"
    BASIC = "Basic"
    CLIENTIDSECRET = "ClientIdSecret"
    GCPBASIC = "GCPBasic"
    NOAUTH = "NoAuth"
    OAUTH = "OAuth"
    OAUTHTOKEN = "OAuthToken"
    PERSONALTOKEN = "PersonalToken"
    CERTAUTH = "CertAuth"
    KEYPAIR = "KeyPair"

    def __str__(self) -> str:
        return str(self.value)
