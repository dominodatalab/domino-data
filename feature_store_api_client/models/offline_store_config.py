from typing import Any, Dict, List, Type, TypeVar

import attr

from ..models.auth_type import AuthType
from ..models.offline_store_config_fields import OfflineStoreConfigFields
from ..models.offline_store_type import OfflineStoreType

T = TypeVar("T", bound="OfflineStoreConfig")


@attr.s(auto_attribs=True)
class OfflineStoreConfig:
    """
    Attributes:
        auth_types (List[AuthType]):
        offline_store_type (OfflineStoreType):
        fields (OfflineStoreConfigFields):
    """

    auth_types: List[AuthType]
    offline_store_type: OfflineStoreType
    fields: OfflineStoreConfigFields
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        auth_types = []
        for auth_types_item_data in self.auth_types:
            auth_types_item = auth_types_item_data.value

            auth_types.append(auth_types_item)

        offline_store_type = self.offline_store_type.value

        fields = self.fields.to_dict()

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "authTypes": auth_types,
                "offlineStoreType": offline_store_type,
                "fields": fields,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        auth_types = []
        _auth_types = d.pop("authTypes")
        for auth_types_item_data in _auth_types:
            auth_types_item = AuthType(auth_types_item_data)

            auth_types.append(auth_types_item)

        offline_store_type = OfflineStoreType(d.pop("offlineStoreType"))

        fields = OfflineStoreConfigFields.from_dict(d.pop("fields"))

        offline_store_config = cls(
            auth_types=auth_types,
            offline_store_type=offline_store_type,
            fields=fields,
        )

        offline_store_config.additional_properties = d
        return offline_store_config

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
