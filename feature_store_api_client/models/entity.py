from typing import Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="Entity")


@attr.s(auto_attribs=True)
class Entity:
    """
    Attributes:
        name (str):
        value_type (str):
        join_key (Union[Unset, str]):
    """

    name: str
    value_type: str
    join_key: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        name = self.name
        value_type = self.value_type
        join_key = self.join_key

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "valueType": value_type,
            }
        )
        if join_key is not UNSET:
            field_dict["joinKey"] = join_key

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        name = d.pop("name")

        value_type = d.pop("valueType")

        join_key = d.pop("joinKey", UNSET)

        entity = cls(
            name=name,
            value_type=value_type,
            join_key=join_key,
        )

        entity.additional_properties = d
        return entity

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
