from typing import Any, Dict, List, Type, TypeVar, Union

import attr

from ..models.create_training_set_request_annotations import CreateTrainingSetRequestAnnotations
from ..models.create_training_set_request_kind import CreateTrainingSetRequestKind
from ..models.create_training_set_request_metadata import CreateTrainingSetRequestMetadata
from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateTrainingSetRequest")


@attr.s(auto_attribs=True)
class CreateTrainingSetRequest:
    """ """

    name: str
    project_id: str
    kind: CreateTrainingSetRequestKind
    metadata: CreateTrainingSetRequestMetadata
    annotations: CreateTrainingSetRequestAnnotations
    description: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        name = self.name
        project_id = self.project_id
        kind = self.kind.value

        metadata = self.metadata.to_dict()

        annotations = self.annotations.to_dict()

        description = self.description

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "projectId": project_id,
                "kind": kind,
                "metadata": metadata,
                "annotations": annotations,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        name = d.pop("name")

        project_id = d.pop("projectId")

        kind = CreateTrainingSetRequestKind(d.pop("kind"))

        metadata = CreateTrainingSetRequestMetadata.from_dict(d.pop("metadata"))

        annotations = CreateTrainingSetRequestAnnotations.from_dict(d.pop("annotations"))

        description = d.pop("description", UNSET)

        create_training_set_request = cls(
            name=name,
            project_id=project_id,
            kind=kind,
            metadata=metadata,
            annotations=annotations,
            description=description,
        )

        create_training_set_request.additional_properties = d
        return create_training_set_request

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
