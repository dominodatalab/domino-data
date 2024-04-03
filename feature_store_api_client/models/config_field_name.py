from enum import Enum


class ConfigFieldName(str, Enum):
    ACCOUNTID = "accountId"
    AUTHENTICATOR = "authenticator"
    BLOBEXPORTLOCATION = "blobExportLocation"
    CLUSTERID = "clusterId"
    CONFIGPATH = "configPath"
    DATABASE = "database"
    DATASETNAME = "datasetName"
    GCSPROJECTNAME = "gcsProjectName"
    GCSSTAGINGLOCATION = "gcsStagingLocation"
    IAMROLE = "iamRole"
    LOCATION = "location"
    REGION = "region"
    ROLE = "role"
    S3STAGINGLOCATION = "s3StagingLocation"
    SCHEMA = "schema"
    STORAGEINTEGRATIONNAME = "storageIntegrationName"
    WAREHOUSE = "warehouse"

    def __str__(self) -> str:
        return str(self.value)
