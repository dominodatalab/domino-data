from typing import Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="Field")


@attr.s(auto_attribs=True)
class Field:
    """
    Attributes:
        is_optional (bool):
        is_overridable (bool):
        name (str):
        alias (Union[Unset, str]):
        is_secret (Union[Unset, bool]):
        regexp (Union[Unset, str]):
        regexp_error_message (Union[Unset, str]):
    """

    is_optional: bool
    is_overridable: bool
    name: str
    alias: Union[Unset, str] = UNSET
    is_secret: Union[Unset, bool] = UNSET
    regexp: Union[Unset, str] = UNSET
    regexp_error_message: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        is_optional = self.is_optional
        is_overridable = self.is_overridable
        name = self.name
        alias = self.alias
        is_secret = self.is_secret
        regexp = self.regexp
        regexp_error_message = self.regexp_error_message

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "isOptional": is_optional,
                "isOverridable": is_overridable,
                "name": name,
            }
        )
        if alias is not UNSET:
            field_dict["alias"] = alias
        if is_secret is not UNSET:
            field_dict["isSecret"] = is_secret
        if regexp is not UNSET:
            field_dict["regexp"] = regexp
        if regexp_error_message is not UNSET:
            field_dict["regexpErrorMessage"] = regexp_error_message

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        is_optional = d.pop("isOptional")

        is_overridable = d.pop("isOverridable")

        name = d.pop("name")

        alias = d.pop("alias", UNSET)

        is_secret = d.pop("isSecret", UNSET)

        regexp = d.pop("regexp", UNSET)

        regexp_error_message = d.pop("regexpErrorMessage", UNSET)

        field = cls(
            is_optional=is_optional,
            is_overridable=is_overridable,
            name=name,
            alias=alias,
            is_secret=is_secret,
            regexp=regexp,
            regexp_error_message=regexp_error_message,
        )

        field.additional_properties = d
        return field

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
