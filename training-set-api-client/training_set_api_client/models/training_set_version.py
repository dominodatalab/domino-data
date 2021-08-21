import datetime
from typing import Any, Dict, List, Type, TypeVar, Union, cast

import attr
from dateutil.parser import isoparse

from ..models.monitoring_meta import MonitoringMeta
from ..models.training_set_version_meta import TrainingSetVersionMeta
from ..types import UNSET, Unset

T = TypeVar("T", bound="TrainingSetVersion")


@attr.s(auto_attribs=True)
class TrainingSetVersion:
    """ """

    id: str
    training_set_id: str
    training_set_name: str
    number: int
    creation_time: datetime.datetime
    url: str
    key_columns: List[str]
    target_columns: List[str]
    exclude_columns: List[str]
    monitoring_meta: MonitoringMeta
    meta: TrainingSetVersionMeta
    pending: bool
    description: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        id = self.id
        training_set_id = self.training_set_id
        training_set_name = self.training_set_name
        number = self.number
        creation_time = self.creation_time.isoformat()

        url = self.url
        key_columns = self.key_columns

        target_columns = self.target_columns

        exclude_columns = self.exclude_columns

        monitoring_meta = self.monitoring_meta.to_dict()

        meta = self.meta.to_dict()

        pending = self.pending
        description = self.description

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "trainingSetId": training_set_id,
                "trainingSetName": training_set_name,
                "number": number,
                "creationTime": creation_time,
                "url": url,
                "keyColumns": key_columns,
                "targetColumns": target_columns,
                "excludeColumns": exclude_columns,
                "monitoringMeta": monitoring_meta,
                "meta": meta,
                "pending": pending,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        id = d.pop("id")

        training_set_id = d.pop("trainingSetId")

        training_set_name = d.pop("trainingSetName")

        number = d.pop("number")

        creation_time = isoparse(d.pop("creationTime"))

        url = d.pop("url")

        key_columns = cast(List[str], d.pop("keyColumns"))

        target_columns = cast(List[str], d.pop("targetColumns"))

        exclude_columns = cast(List[str], d.pop("excludeColumns"))

        monitoring_meta = MonitoringMeta.from_dict(d.pop("monitoringMeta"))

        meta = TrainingSetVersionMeta.from_dict(d.pop("meta"))

        pending = d.pop("pending")

        description = d.pop("description", UNSET)

        training_set_version = cls(
            id=id,
            training_set_id=training_set_id,
            training_set_name=training_set_name,
            number=number,
            creation_time=creation_time,
            url=url,
            key_columns=key_columns,
            target_columns=target_columns,
            exclude_columns=exclude_columns,
            monitoring_meta=monitoring_meta,
            meta=meta,
            pending=pending,
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
