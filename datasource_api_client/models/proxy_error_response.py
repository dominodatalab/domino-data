from typing import Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="ProxyErrorResponse")


@attr.s(auto_attribs=True)
class ProxyErrorResponse:
    """
    Attributes:
        error_type (Union[Unset, str]):
        sub_type (Union[Unset, str]):
        raw_error (Union[Unset, str]):
    """

    error_type: Union[Unset, str] = UNSET
    sub_type: Union[Unset, str] = UNSET
    raw_error: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        error_type = self.error_type
        sub_type = self.sub_type
        raw_error = self.raw_error

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if error_type is not UNSET:
            field_dict["errorType"] = error_type
        if sub_type is not UNSET:
            field_dict["subType"] = sub_type
        if raw_error is not UNSET:
            field_dict["rawError"] = raw_error

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        error_type = d.pop("errorType", UNSET)

        sub_type = d.pop("subType", UNSET)

        raw_error = d.pop("rawError", UNSET)

        proxy_error_response = cls(
            error_type=error_type,
            sub_type=sub_type,
            raw_error=raw_error,
        )

        proxy_error_response.additional_properties = d
        return proxy_error_response

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
