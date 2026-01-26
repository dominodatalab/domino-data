from enum import Enum


class DatasourceDtoAuthType(str, Enum):
    AWSIAMBASIC = "AWSIAMBasic"
    AWSIAMBASICNOOVERRIDE = "AWSIAMBasicNoOverride"
    AWSIAMROLE = "AWSIAMRole"
    AWSIAMROLEWITHUSERNAME = "AWSIAMRoleWithUsername"
    AZUREBASIC = "AzureBasic"
    BASIC = "Basic"
    CERTAUTH = "CertAuth"
    CLIENTIDSECRET = "ClientIdSecret"
    CUSTOMDSN = "CustomDSN"
    GCPBASIC = "GCPBasic"
    KEYPAIR = "KeyPair"
    NOAUTH = "NoAuth"
    OAUTH = "OAuth"
    OAUTHTOKEN = "OAuthToken"
    PERSONALTOKEN = "PersonalToken"

    def __str__(self) -> str:
        return str(self.value)
