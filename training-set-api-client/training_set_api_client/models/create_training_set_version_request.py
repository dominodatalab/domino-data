from typing import Any, Dict, List, Type, TypeVar, Union, cast

import attr

from ..models.create_training_set_version_request_meta import CreateTrainingSetVersionRequestMeta
from ..models.monitoring_meta import MonitoringMeta
from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateTrainingSetVersionRequest")


@attr.s(auto_attribs=True)
class CreateTrainingSetVersionRequest:
    """ """

    project_owner_username: str
    project_name: str
    key_columns: List[str]
    target_columns: List[str]
    exclude_columns: List[str]
    monitoring_meta: MonitoringMeta
    meta: CreateTrainingSetVersionRequestMeta
    name: Union[Unset, str] = UNSET
    description: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        project_owner_username = self.project_owner_username
        project_name = self.project_name
        key_columns = self.key_columns

        target_columns = self.target_columns

        exclude_columns = self.exclude_columns

        monitoring_meta = self.monitoring_meta.to_dict()

        meta = self.meta.to_dict()

        name = self.name
        description = self.description

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "projectOwnerUsername": project_owner_username,
                "projectName": project_name,
                "keyColumns": key_columns,
                "targetColumns": target_columns,
                "excludeColumns": exclude_columns,
                "monitoringMeta": monitoring_meta,
                "meta": meta,
            }
        )
        if name is not UNSET:
            field_dict["name"] = name
        if description is not UNSET:
            field_dict["description"] = description

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        project_owner_username = d.pop("projectOwnerUsername")

        project_name = d.pop("projectName")

        key_columns = cast(List[str], d.pop("keyColumns"))

        target_columns = cast(List[str], d.pop("targetColumns"))

        exclude_columns = cast(List[str], d.pop("excludeColumns"))

        monitoring_meta = MonitoringMeta.from_dict(d.pop("monitoringMeta"))

        meta = CreateTrainingSetVersionRequestMeta.from_dict(d.pop("meta"))

        name = d.pop("name", UNSET)

        description = d.pop("description", UNSET)

        create_training_set_version_request = cls(
            project_owner_username=project_owner_username,
            project_name=project_name,
            key_columns=key_columns,
            target_columns=target_columns,
            exclude_columns=exclude_columns,
            monitoring_meta=monitoring_meta,
            meta=meta,
            name=name,
            description=description,
        )

        create_training_set_version_request.additional_properties = d
        return create_training_set_version_request

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
