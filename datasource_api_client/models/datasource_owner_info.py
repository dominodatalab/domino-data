from typing import Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="DatasourceOwnerInfo")


@attr.s(auto_attribs=True)
class DatasourceOwnerInfo:
    """ """

    owner_name: Union[Unset, str] = UNSET
    owner_email: Union[Unset, str] = UNSET
    is_owner_admin: Union[Unset, bool] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        owner_name = self.owner_name
        owner_email = self.owner_email
        is_owner_admin = self.is_owner_admin

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if owner_name is not UNSET:
            field_dict["ownerName"] = owner_name
        if owner_email is not UNSET:
            field_dict["ownerEmail"] = owner_email
        if is_owner_admin is not UNSET:
            field_dict["isOwnerAdmin"] = is_owner_admin

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        owner_name = d.pop("ownerName", UNSET)

        owner_email = d.pop("ownerEmail", UNSET)

        is_owner_admin = d.pop("isOwnerAdmin", UNSET)

        datasource_owner_info = cls(
            owner_name=owner_name,
            owner_email=owner_email,
            is_owner_admin=is_owner_admin,
        )

        datasource_owner_info.additional_properties = d
        return datasource_owner_info

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
