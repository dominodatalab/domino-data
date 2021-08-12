import datetime
from typing import Any, Dict, List, Type, TypeVar, Union, cast

import attr
from dateutil.parser import isoparse

from ..models.training_set_version_metadata import TrainingSetVersionMetadata
from ..types import UNSET, Unset

T = TypeVar("T", bound="TrainingSetVersion")


@attr.s(auto_attribs=True)
class TrainingSetVersion:
    """ """

    id: str
    training_set_id: str
    creation_time: datetime.datetime
    url: str
    timestamp_column: str
    independent_vars: List[str]
    target_vars: List[str]
    continuous_vars: List[str]
    categorical_vars: List[str]
    ordinal_vars: List[str]
    metadata: TrainingSetVersionMetadata
    pending: bool
    name: Union[Unset, str] = UNSET
    description: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        id = self.id
        training_set_id = self.training_set_id
        creation_time = self.creation_time.isoformat()

        url = self.url
        timestamp_column = self.timestamp_column
        independent_vars = self.independent_vars

        target_vars = self.target_vars

        continuous_vars = self.continuous_vars

        categorical_vars = self.categorical_vars

        ordinal_vars = self.ordinal_vars

        metadata = self.metadata.to_dict()

        pending = self.pending
        name = self.name
        description = self.description

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "trainingSetId": training_set_id,
                "creationTime": creation_time,
                "url": url,
                "timestampColumn": timestamp_column,
                "independentVars": independent_vars,
                "targetVars": target_vars,
                "continuousVars": continuous_vars,
                "categoricalVars": categorical_vars,
                "ordinalVars": ordinal_vars,
                "metadata": metadata,
                "pending": pending,
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
        id = d.pop("id")

        training_set_id = d.pop("trainingSetId")

        creation_time = isoparse(d.pop("creationTime"))

        url = d.pop("url")

        timestamp_column = d.pop("timestampColumn")

        independent_vars = cast(List[str], d.pop("independentVars"))

        target_vars = cast(List[str], d.pop("targetVars"))

        continuous_vars = cast(List[str], d.pop("continuousVars"))

        categorical_vars = cast(List[str], d.pop("categoricalVars"))

        ordinal_vars = cast(List[str], d.pop("ordinalVars"))

        metadata = TrainingSetVersionMetadata.from_dict(d.pop("metadata"))

        pending = d.pop("pending")

        name = d.pop("name", UNSET)

        description = d.pop("description", UNSET)

        training_set_version = cls(
            id=id,
            training_set_id=training_set_id,
            creation_time=creation_time,
            url=url,
            timestamp_column=timestamp_column,
            independent_vars=independent_vars,
            target_vars=target_vars,
            continuous_vars=continuous_vars,
            categorical_vars=categorical_vars,
            ordinal_vars=ordinal_vars,
            metadata=metadata,
            pending=pending,
            name=name,
            description=description,
        )

        training_set_version.additional_properties = d
        return training_set_version

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
