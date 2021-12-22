from typing import Any, Dict, List, Type, TypeVar, Union

import attr

from ..models.datasource_config import DatasourceConfig
from ..types import UNSET, Unset

T = TypeVar("T", bound="KeyRequest")


@attr.s(auto_attribs=True)
class KeyRequest:
    """
    Attributes:
        datasource_id (str):
        is_read_write (bool):
        object_key (str):
        config_overwrites (Union[Unset, DatasourceConfig]):
        credential_overwrites (Union[Unset, DatasourceConfig]):
    """

    datasource_id: str
    is_read_write: bool
    object_key: str
    config_overwrites: Union[Unset, DatasourceConfig] = UNSET
    credential_overwrites: Union[Unset, DatasourceConfig] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        datasource_id = self.datasource_id
        is_read_write = self.is_read_write
        object_key = self.object_key
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
                "isReadWrite": is_read_write,
                "objectKey": object_key,
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

        is_read_write = d.pop("isReadWrite")

        object_key = d.pop("objectKey")

        _config_overwrites = d.pop("configOverwrites", UNSET)
        config_overwrites: Union[Unset, DatasourceConfig]
        if isinstance(_config_overwrites, Unset):
            config_overwrites = UNSET
        else:
            config_overwrites = DatasourceConfig.from_dict(_config_overwrites)

        _credential_overwrites = d.pop("credentialOverwrites", UNSET)
        credential_overwrites: Union[Unset, DatasourceConfig]
        if isinstance(_credential_overwrites, Unset):
            credential_overwrites = UNSET
        else:
            credential_overwrites = DatasourceConfig.from_dict(_credential_overwrites)

        key_request = cls(
            datasource_id=datasource_id,
            is_read_write=is_read_write,
            object_key=object_key,
            config_overwrites=config_overwrites,
            credential_overwrites=credential_overwrites,
        )

        key_request.additional_properties = d
        return key_request

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
