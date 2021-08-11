import datetime
from typing import Any, Dict, List, Type, TypeVar, Union

import attr
from dateutil.parser import isoparse

from ..models.training_set_annotations import TrainingSetAnnotations
from ..models.training_set_kind import TrainingSetKind
from ..models.training_set_metadata import TrainingSetMetadata
from ..types import UNSET, Unset

T = TypeVar("T", bound="TrainingSet")


@attr.s(auto_attribs=True)
class TrainingSet:
    """ """

    id: str
    name: str
    kind: TrainingSetKind
    creation_time: datetime.datetime
    owner_id: str
    metadata: TrainingSetMetadata
    annotations: TrainingSetAnnotations
    archived: bool
    project_id: Union[Unset, str] = UNSET
    description: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        id = self.id
        name = self.name
        kind = self.kind.value

        creation_time = self.creation_time.isoformat()

        owner_id = self.owner_id
        metadata = self.metadata.to_dict()

        annotations = self.annotations.to_dict()

        archived = self.archived
        project_id = self.project_id
        description = self.description

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "kind": kind,
                "creationTime": creation_time,
                "ownerId": owner_id,
                "metadata": metadata,
                "annotations": annotations,
                "archived": archived,
            }
        )
        if project_id is not UNSET:
            field_dict["projectId"] = project_id
        if description is not UNSET:
            field_dict["description"] = description

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        id = d.pop("id")

        name = d.pop("name")

        kind = TrainingSetKind(d.pop("kind"))

        creation_time = isoparse(d.pop("creationTime"))

        owner_id = d.pop("ownerId")

        metadata = TrainingSetMetadata.from_dict(d.pop("metadata"))

        annotations = TrainingSetAnnotations.from_dict(d.pop("annotations"))

        archived = d.pop("archived")

        project_id = d.pop("projectId", UNSET)

        description = d.pop("description", UNSET)

        training_set = cls(
            id=id,
            name=name,
            kind=kind,
            creation_time=creation_time,
            owner_id=owner_id,
            metadata=metadata,
            annotations=annotations,
            archived=archived,
            project_id=project_id,
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
