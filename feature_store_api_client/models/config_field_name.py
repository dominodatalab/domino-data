from enum import Enum


class ConfigFieldName(str, Enum):
    ACCOUNTID = "accountId"
    ROLE = "role"
    WAREHOUSE = "warehouse"
    DATABASE = "database"
    CLUSTERID = "clusterId"
    REGION = "region"
    S3STAGINGLOCATION = "s3StagingLocation"
    IAMROLE = "iamRole"
    DATASETNAME = "datasetName"
    GCSSTAGINGLOCATION = "gcsStagingLocation"
    LOCATION = "location"
    GCSPROJECTNAME = "gcsProjectName"
    AUTHENTICATOR = "authenticator"
    BLOBEXPORTLOCATION = "blobExportLocation"
    CONFIGPATH = "configPath"
    SCHEMA = "schema"
    STORAGEINTEGRATIONNAME = "storageIntegrationName"

    def __str__(self) -> str:
        return str(self.value)
