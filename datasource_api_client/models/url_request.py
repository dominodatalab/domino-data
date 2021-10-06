from typing import Any, Dict, List, Type, TypeVar, Union

import attr

from ..models.url_request_config_overwrites import UrlRequestConfigOverwrites
from ..models.url_request_credential_overwrites import UrlRequestCredentialOverwrites
from ..types import UNSET, Unset

T = TypeVar("T", bound="UrlRequest")


@attr.s(auto_attribs=True)
class UrlRequest:
    """ """

    datasource_id: str
    object_key: str
    is_read_write: bool
    config_overwrites: Union[Unset, UrlRequestConfigOverwrites] = UNSET
    credential_overwrites: Union[Unset, UrlRequestCredentialOverwrites] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        datasource_id = self.datasource_id
        object_key = self.object_key
        is_read_write = self.is_read_write
        config_overwrites: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.config_overwrites, Unset):
            config_overwrites = self.config_overwrites.to_dict()

        credential_overwrites: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.credential_overwrites, Unset):
            credential_overwrites = self.credential_overwrites.to_dict()

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "datasourceId": datasource_id,
                "objectKey": object_key,
                "isReadWrite": is_read_write,
            }
        )
        if config_overwrites is not UNSET:
            field_dict["configOverwrites"] = config_overwrites
        if credential_overwrites is not UNSET:
            field_dict["credentialOverwrites"] = credential_overwrites

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        datasource_id = d.pop("datasourceId")

        object_key = d.pop("objectKey")

        is_read_write = d.pop("isReadWrite")

        _config_overwrites = d.pop("configOverwrites", UNSET)
        config_overwrites: Union[Unset, UrlRequestConfigOverwrites]
        if isinstance(_config_overwrites, Unset):
            config_overwrites = UNSET
        else:
            config_overwrites = UrlRequestConfigOverwrites.from_dict(_config_overwrites)

        _credential_overwrites = d.pop("credentialOverwrites", UNSET)
        credential_overwrites: Union[Unset, UrlRequestCredentialOverwrites]
        if isinstance(_credential_overwrites, Unset):
            credential_overwrites = UNSET
        else:
            credential_overwrites = UrlRequestCredentialOverwrites.from_dict(_credential_overwrites)

        url_request = cls(
            datasource_id=datasource_id,
            object_key=object_key,
            is_read_write=is_read_write,
            config_overwrites=config_overwrites,
            credential_overwrites=credential_overwrites,
        )

        url_request.additional_properties = d
        return url_request

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
