from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.auth_type import AuthType

if TYPE_CHECKING:
    from ..models.auth_config_fields import AuthConfigFields
    from ..models.auth_config_meta import AuthConfigMeta


T = TypeVar("T", bound="AuthConfig")


@_attrs_define
class AuthConfig:
    """
    Attributes:
        auth_type (AuthType):
        fields (AuthConfigFields):
        meta (AuthConfigMeta):
    """

    auth_type: AuthType
    fields: "AuthConfigFields"
    meta: "AuthConfigMeta"
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        auth_type = self.auth_type.value

        fields = self.fields.to_dict()

        meta = self.meta.to_dict()

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "authType": auth_type,
                "fields": fields,
                "meta": meta,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.auth_config_fields import AuthConfigFields
        from ..models.auth_config_meta import AuthConfigMeta

        d = src_dict.copy()
        auth_type = AuthType(d.pop("authType"))

        fields = AuthConfigFields.from_dict(d.pop("fields"))

        meta = AuthConfigMeta.from_dict(d.pop("meta"))

        auth_config = cls(
            auth_type=auth_type,
            fields=fields,
            meta=meta,
        )

        auth_config.additional_properties = d
        return auth_config

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
