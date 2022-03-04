from enum import Enum


class DatasourceDtoAuthType(str, Enum):
    AZUREBASIC = "AzureBasic"
    BASIC = "Basic"
    IAMBASIC = "IAMBasic"
    IAMPASSTHROUGH = "IAMPassthrough"
    GCPBASIC = "GCPBasic"
    OAUTHPASSTHROUGH = "OAuthPassthrough"

    def __str__(self) -> str:
        return str(self.value)
