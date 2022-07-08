from typing import Any, Dict, List, Type, TypeVar, Union

import attr

from ..models.datasource_config import DatasourceConfig
from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateDatasourceRequest")


@attr.s(auto_attribs=True)
class CreateDatasourceRequest:
    """
    Attributes:
        name (str):
        datasource_type (str):
        description (Union[Unset, str]):
        project_id (Union[Unset, str]):
        account_name (Union[Unset, str]):
        database (Union[Unset, str]):
        schema (Union[Unset, str]):
        warehouse (Union[Unset, str]):
        role (Union[Unset, str]):
        host (Union[Unset, str]):
        port (Union[Unset, str]):
        bucket (Union[Unset, str]):
        region (Union[Unset, str]):
        project (Union[Unset, str]):
        credentialType (str):
        auth_type (str):
        engine_type (str):
        engine_catalog_entry_name (Union[Unset, str]):
        visible_credential (Union[Unset, str]):
        secret_credential (Union[Unset, str]):
        is_everyone (boolean):
        user_ids (List[str])
    """

    name: str
    datasource_type: str
    description: Union[Unset, str] = UNSET
    project_id: Union[Unset, str] = UNSET
    account_name: Union[Unset, str] = UNSET
    database: Union[Unset, str] = UNSET
    schema: Union[Unset, str] = UNSET
    warehouse: Union[Unset, str] = UNSET
    role: Union[Unset, str] = UNSET
    host: Union[Unset, str] = UNSET
    port: Union[Unset, str] = UNSET
    bucket: Union[Unset, str] = UNSET
    region: Union[Unset, str] = UNSET
    project: Union[Unset, str] = UNSET
    credential_type: str
    auth_type: str
    engine_type: str
    engine_catalog_entry_name: Union[Unset, str] = UNSET
    visible_credential: Union[Unset, str] = UNSET
    secret_credential: Union[Unset, str] = UNSET
    is_everyone: boolean
    user_ids: List[str]
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        name = self.name
        datasource_type = self.datasource_type
        credential_type = self.credential_type
        auth_type = self.auth_type
        engine_type = self.engine_type
        is_everyone = self.is_everyone
        user_ids = self.user_ids

        description: Union[Unset, str] = UNSET
        if not isinstance(self.description, Unset):
            description = self.description.to_dict()

        project_id: Union[Unset, str] = UNSET
        if not isinstance(self.project_id, Unset):
            project_id = self.project_id.to_dict()

        account_name: Union[Unset, str] = UNSET
        if not isinstance(self.account_name, Unset):
            account_name = self.account_name.to_dict()

        database: Union[Unset, str] = UNSET
        if not isinstance(self.database, Unset):
            database = self.database.to_dict()

        schema: Union[Unset, str] = UNSET
        if not isinstance(self.schema, Unset):
            schema = self.schema.to_dict()

        warehouse: Union[Unset, str] = UNSET
        if not isinstance(self.warehouse, Unset):
            warehouse = self.warehouse.to_dict()

        role: Union[Unset, str] = UNSET
        if not isinstance(self.role, Unset):
            role = self.role.to_dict()

        host: Union[Unset, str] = UNSET
        if not isinstance(self.host, Unset):
            host = self.host.to_dict()

        port: Union[Unset, str] = UNSET
        if not isinstance(self.port, Unset):
            port = self.port.to_dict()

        bucket: Union[Unset, str] = UNSET
        if not isinstance(self.bucket, Unset):
            bucket = self.bucket.to_dict()

        region: Union[Unset, str] = UNSET
        if not isinstance(self.region, Unset):
            region = self.region.to_dict()

        project: Union[Unset, str] = UNSET
        if not isinstance(self.project, Unset):
            project = self.project.to_dict()

        engine_catalog_entry_name: Union[Unset, str] = UNSET
        if not isinstance(self.engine_catalog_entry_name, Unset):
            engine_catalog_entry_name = self.engine_catalog_entry_name.to_dict()

        visible_credential: Union[Unset, str] = UNSET
        if not isinstance(self.visible_credential, Unset):
            region = self.visible_credential.to_dict()

        secret_credential: Union[Unset, str] = UNSET
        if not isinstance(self.secret_credential, Unset):
            secret_credential = self.secret_credential.to_dict()

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "datasourceType": datasource_type,
                "credentialType": credential_type,
                "authType": auth_type,
                "engineType": engine_type,
                "isEveryone": is_everyone,
                "userIds": user_ids,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description

        if project_id is not UNSET:
            field_dict["projectId"] = project_id

        if account_name is not UNSET:
            field_dict["accountName"] = account_name

        if database is not UNSET:
            field_dict["database"] = database

        if schema is not UNSET:
            field_dict["schema"] = schema

        if warehouse is not UNSET:
            field_dict["warehouse"] = warehouse

        if role is not UNSET:
            field_dict["role"] = role

        if host is not UNSET:
            field_dict["host"] = host

        if port is not UNSET:
            field_dict["port"] = port

        if bucket is not UNSET:
            field_dict["bucket"] = bucket

        if project is not UNSET:
            field_dict["project"] = project

        if engine_catalog_entry_name is not UNSET:
            field_dict["engineCatalogEntryName"] = engine_catalog_entry_name

        if visible_credential is not UNSET:
            field_dict["visibleCredential"] = visible_credential

        if secret_credential is not UNSET:
            field_dict["secretCredential"] = secret_credential

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()

        name = d.pop("name")

        datasource_type = d.pop("datasourceType")

        credential_type = d.pop("credentialType")

        auth_type = d.pop("authType")

        engine_type = d.pop("engineType")

        is_everyone = d.pop("isEveryone")

        user_ids = cast(List[str], d.pop("userIds"))

        description = d.pop("description", UNSET)

        project_id = d.pop("projectId", UNSET)

        account_name = d.pop("accountName", UNSET)

        database = d.pop("database", UNSET)

        schema = d.pop("schema", UNSET)

        warehouse = d.pop("warehouse", UNSET)

        role = d.pop("role", UNSET)

        host = d.pop("host", UNSET)

        port = d.pop("port", UNSET)

        bucket = d.pop("bucket", UNSET)

        region = d.pop("region", UNSET)

        project = d.pop("project", UNSET)

        engine_catalog_entry_name = d.pop("engineCatalogEntryName", UNSET)

        visible_credential = d.pop("visibleCredential", UNSET)

        secret_credential = d.pop("secretCredential", UNSET)

        create_datasource_request = cls(
            name=name,
            datasource_type=datasource_type,
            description=description,
            project_id=project_id,
            account_name=account_name,
            database=database,
            schema=schema,
            warehouse=warehouse,
            role=role,
            host=host,
            port=port,
            bucket=bucket,
            region=region,
            project=project,
            credential_type=credential_type,
            auth_type=auth_type,
            engine_type=engine_type,
            engine_catalog_entry_name=engine_catalog_entry_name,
            visible_credential=visible_credential,
            secret_credential=secret_credential,
            is_everyone=is_everyone,
            user_ids=user_ids,
        )

        create_datasource_request.additional_properties = d
        return create_datasource_request

    @property
    def additional_keys(self) -> List[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    #     def __setitem__(self, key (str): value: Any) -> None:
    #         self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
