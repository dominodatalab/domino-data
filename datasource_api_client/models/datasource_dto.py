from typing import Any, Dict, List, Type, TypeVar, Union, cast

import attr

from ..models.datasource_config import DatasourceConfig
from ..models.datasource_dto_added_by import DatasourceDtoAddedBy
from ..models.datasource_dto_credential_type import DatasourceDtoCredentialType
from ..models.datasource_dto_data_source_type import DatasourceDtoDataSourceType
from ..models.datasource_dto_status import DatasourceDtoStatus
from ..models.datasource_owner_info import DatasourceOwnerInfo
from ..types import UNSET, Unset

T = TypeVar("T", bound="DatasourceDto")


@attr.s(auto_attribs=True)
class DatasourceDto:
    """ """

    added_by: DatasourceDtoAddedBy
    config: DatasourceConfig
    credential_type: DatasourceDtoCredentialType
    data_source_type: DatasourceDtoDataSourceType
    id: str
    is_everyone: bool
    last_updated: int
    last_updated_by: str
    name: str
    owner_id: str
    owner_info: DatasourceOwnerInfo
    project_ids: List[str]
    status: DatasourceDtoStatus
    user_ids: List[str]
    description: Union[Unset, None, str] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        added_by = self.added_by.to_dict()

        config = self.config.to_dict()

        credential_type = self.credential_type.value

        data_source_type = self.data_source_type.value

        id = self.id
        is_everyone = self.is_everyone
        last_updated = self.last_updated
        last_updated_by = self.last_updated_by
        name = self.name
        owner_id = self.owner_id
        owner_info = self.owner_info.to_dict()

        project_ids = self.project_ids

        status = self.status.value

        user_ids = self.user_ids

        description = self.description

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "addedBy": added_by,
                "config": config,
                "credentialType": credential_type,
                "dataSourceType": data_source_type,
                "id": id,
                "isEveryone": is_everyone,
                "lastUpdated": last_updated,
                "lastUpdatedBy": last_updated_by,
                "name": name,
                "ownerId": owner_id,
                "ownerInfo": owner_info,
                "projectIds": project_ids,
                "status": status,
                "userIds": user_ids,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        added_by = DatasourceDtoAddedBy.from_dict(d.pop("addedBy"))

        config = DatasourceConfig.from_dict(d.pop("config"))

        credential_type = DatasourceDtoCredentialType(d.pop("credentialType"))

        data_source_type = DatasourceDtoDataSourceType(d.pop("dataSourceType"))

        id = d.pop("id")

        is_everyone = d.pop("isEveryone")

        last_updated = d.pop("lastUpdated")

        last_updated_by = d.pop("lastUpdatedBy")

        name = d.pop("name")

        owner_id = d.pop("ownerId")

        owner_info = DatasourceOwnerInfo.from_dict(d.pop("ownerInfo"))

        project_ids = cast(List[str], d.pop("projectIds"))

        status = DatasourceDtoStatus(d.pop("status"))

        user_ids = cast(List[str], d.pop("userIds"))

        description = d.pop("description", UNSET)

        datasource_dto = cls(
            added_by=added_by,
            config=config,
            credential_type=credential_type,
            data_source_type=data_source_type,
            id=id,
            is_everyone=is_everyone,
            last_updated=last_updated,
            last_updated_by=last_updated_by,
            name=name,
            owner_id=owner_id,
            owner_info=owner_info,
            project_ids=project_ids,
            status=status,
            user_ids=user_ids,
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
