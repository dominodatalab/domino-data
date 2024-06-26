from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.monitoring_meta import MonitoringMeta
    from ..models.update_training_set_version_request_meta import (
        UpdateTrainingSetVersionRequestMeta,
    )


T = TypeVar("T", bound="UpdateTrainingSetVersionRequest")


@_attrs_define
class UpdateTrainingSetVersionRequest:
    """
    Attributes:
        key_columns (List[str]):
        target_columns (List[str]):
        exclude_columns (List[str]):
        monitoring_meta (MonitoringMeta):
        meta (UpdateTrainingSetVersionRequestMeta):
        pending (bool):
        description (Union[Unset, str]):
    """

    key_columns: List[str]
    target_columns: List[str]
    exclude_columns: List[str]
    monitoring_meta: "MonitoringMeta"
    meta: "UpdateTrainingSetVersionRequestMeta"
    pending: bool
    description: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
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
        from ..models.monitoring_meta import MonitoringMeta
        from ..models.update_training_set_version_request_meta import (
            UpdateTrainingSetVersionRequestMeta,
        )

        d = src_dict.copy()
        key_columns = cast(List[str], d.pop("keyColumns"))

        target_columns = cast(List[str], d.pop("targetColumns"))

        exclude_columns = cast(List[str], d.pop("excludeColumns"))

        monitoring_meta = MonitoringMeta.from_dict(d.pop("monitoringMeta"))

        meta = UpdateTrainingSetVersionRequestMeta.from_dict(d.pop("meta"))

        pending = d.pop("pending")

        description = d.pop("description", UNSET)

        update_training_set_version_request = cls(
            key_columns=key_columns,
            target_columns=target_columns,
            exclude_columns=exclude_columns,
            monitoring_meta=monitoring_meta,
            meta=meta,
            pending=pending,
            description=description,
        )

        update_training_set_version_request.additional_properties = d
        return update_training_set_version_request

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
