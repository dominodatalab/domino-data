import datetime
from typing import Any, Dict, List, Type, TypeVar, Union, cast

import attr
from dateutil.parser import isoparse

from ..models.training_set_meta import TrainingSetMeta
from ..types import UNSET, Unset

T = TypeVar("T", bound="TrainingSet")


@attr.s(auto_attribs=True)
class TrainingSet:
    """ """

    id: str
    project_id: str
    name: str
    creation_time: datetime.datetime
    owner_id: str
    owner_name: str
    collaborator_ids: List[str]
    collaborator_names: List[str]
    meta: TrainingSetMeta
    description: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        id = self.id
        project_id = self.project_id
        name = self.name
        creation_time = self.creation_time.isoformat()

        owner_id = self.owner_id
        owner_name = self.owner_name
        collaborator_ids = self.collaborator_ids

        collaborator_names = self.collaborator_names

        meta = self.meta.to_dict()

        description = self.description

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "projectId": project_id,
                "name": name,
                "creationTime": creation_time,
                "ownerId": owner_id,
                "ownerName": owner_name,
                "collaboratorIds": collaborator_ids,
                "collaboratorNames": collaborator_names,
                "meta": meta,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        id = d.pop("id")

        project_id = d.pop("projectId")

        name = d.pop("name")

        creation_time = isoparse(d.pop("creationTime"))

        owner_id = d.pop("ownerId")

        owner_name = d.pop("ownerName")

        collaborator_ids = cast(List[str], d.pop("collaboratorIds"))

        collaborator_names = cast(List[str], d.pop("collaboratorNames"))

        meta = TrainingSetMeta.from_dict(d.pop("meta"))

        description = d.pop("description", UNSET)

        training_set = cls(
            id=id,
            project_id=project_id,
            name=name,
            creation_time=creation_time,
            owner_id=owner_id,
            owner_name=owner_name,
            collaborator_ids=collaborator_ids,
            collaborator_names=collaborator_names,
            meta=meta,
            description=description,
        )

        training_set.additional_properties = d
        return training_set

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
