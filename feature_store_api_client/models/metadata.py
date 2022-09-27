from typing import Any, Dict, List, Type, TypeVar

import attr

T = TypeVar("T", bound="Metadata")


@attr.s(auto_attribs=True)
class Metadata:
    """
    Attributes:
        created_at_millis (int):
        last_updated_millis (int):
    """

    created_at_millis: int
    last_updated_millis: int
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        created_at_millis = self.created_at_millis
        last_updated_millis = self.last_updated_millis

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "createdAtMillis": created_at_millis,
                "lastUpdatedMillis": last_updated_millis,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        created_at_millis = d.pop("createdAtMillis")

        last_updated_millis = d.pop("lastUpdatedMillis")

        metadata = cls(
            created_at_millis=created_at_millis,
            last_updated_millis=last_updated_millis,
        )

        metadata.additional_properties = d
        return metadata

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
