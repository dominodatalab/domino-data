from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.feature_tags import FeatureTags


T = TypeVar("T", bound="Feature")


@_attrs_define
class Feature:
    """
    Attributes:
        name (str):
        dtype (str):
        tags (FeatureTags):
    """

    name: str
    dtype: str
    tags: "FeatureTags"
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        name = self.name

        dtype = self.dtype

        tags = self.tags.to_dict()

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "dtype": dtype,
                "tags": tags,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.feature_tags import FeatureTags

        d = src_dict.copy()
        name = d.pop("name")

        dtype = d.pop("dtype")

        tags = FeatureTags.from_dict(d.pop("tags"))

        feature = cls(
            name=name,
            dtype=dtype,
            tags=tags,
        )

        feature.additional_properties = d
        return feature

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
