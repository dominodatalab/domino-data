from typing import Any, Dict, List, Type, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="MonitoringMeta")


@_attrs_define
class MonitoringMeta:
    """
    Attributes:
        timestamp_columns (List[str]):
        categorical_columns (List[str]):
        ordinal_columns (List[str]):
    """

    timestamp_columns: List[str]
    categorical_columns: List[str]
    ordinal_columns: List[str]
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        timestamp_columns = self.timestamp_columns

        categorical_columns = self.categorical_columns

        ordinal_columns = self.ordinal_columns

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "timestampColumns": timestamp_columns,
                "categoricalColumns": categorical_columns,
                "ordinalColumns": ordinal_columns,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        timestamp_columns = cast(List[str], d.pop("timestampColumns"))

        categorical_columns = cast(List[str], d.pop("categoricalColumns"))

        ordinal_columns = cast(List[str], d.pop("ordinalColumns"))

        monitoring_meta = cls(
            timestamp_columns=timestamp_columns,
            categorical_columns=categorical_columns,
            ordinal_columns=ordinal_columns,
        )

        monitoring_meta.additional_properties = d
        return monitoring_meta

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
