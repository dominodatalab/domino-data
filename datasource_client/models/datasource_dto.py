from typing import Any, Dict, List, Type, TypeVar, Union, cast

import attr

from ..models.datasource_config import DatasourceConfig
from ..models.datasource_dto_credential_type import DatasourceDtoCredentialType
from ..models.datasource_dto_data_source_type import DatasourceDtoDataSourceType
from ..models.datasource_dto_status import DatasourceDtoStatus
from ..types import UNSET, Unset

T = TypeVar("T", bound="DatasourceDto")


@attr.s(auto_attribs=True)
class DatasourceDto:
    """ """

    id: str
    name: str
    owner_id: str
    owner_name: str
    added_by: str
    data_source_type: DatasourceDtoDataSourceType
    config: DatasourceConfig
    credential_type: DatasourceDtoCredentialType
    last_updated: int
    last_updated_by: str
    is_everyone: bool
    user_ids: List[str]
    project_ids: List[str]
    status: DatasourceDtoStatus
    description: Union[Unset, None, str] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        id = self.id
        name = self.name
        owner_id = self.owner_id
        owner_name = self.owner_name
        added_by = self.added_by
        data_source_type = self.data_source_type.value

        config = self.config.to_dict()

        credential_type = self.credential_type.value

        last_updated = self.last_updated
        last_updated_by = self.last_updated_by
        is_everyone = self.is_everyone
        user_ids = self.user_ids

        project_ids = self.project_ids

        status = self.status.value

        description = self.description

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "ownerId": owner_id,
                "ownerName": owner_name,
                "addedBy": added_by,
                "dataSourceType": data_source_type,
                "config": config,
                "credentialType": credential_type,
                "lastUpdated": last_updated,
                "lastUpdatedBy": last_updated_by,
                "isEveryone": is_everyone,
                "userIds": user_ids,
                "projectIds": project_ids,
                "status": status,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        id = d.pop("id")

        name = d.pop("name")

        owner_id = d.pop("ownerId")

        owner_name = d.pop("ownerName")

        added_by = d.pop("addedBy")

        data_source_type = DatasourceDtoDataSourceType(d.pop("dataSourceType"))

        config = DatasourceConfig.from_dict(d.pop("config"))

        credential_type = DatasourceDtoCredentialType(d.pop("credentialType"))

        last_updated = d.pop("lastUpdated")

        last_updated_by = d.pop("lastUpdatedBy")

        is_everyone = d.pop("isEveryone")

        user_ids = cast(List[str], d.pop("userIds"))

        project_ids = cast(List[str], d.pop("projectIds"))

        status = DatasourceDtoStatus(d.pop("status"))

        description = d.pop("description", UNSET)

        datasource_dto = cls(
            id=id,
            name=name,
            owner_id=owner_id,
            owner_name=owner_name,
            added_by=added_by,
            data_source_type=data_source_type,
            config=config,
            credential_type=credential_type,
            last_updated=last_updated,
            last_updated_by=last_updated_by,
            is_everyone=is_everyone,
            user_ids=user_ids,
            project_ids=project_ids,
            status=status,
            description=description,
        )

        datasource_dto.additional_properties = d
        return datasource_dto

    @property
    def additional_keys(self) -> List[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
