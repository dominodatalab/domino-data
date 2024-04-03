from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.datasource_config import DatasourceConfig


T = TypeVar("T", bound="ListRequest")


@_attrs_define
class ListRequest:
    """
    Attributes:
        datasource_id (str):
        prefix (str):
        config_overwrites (Union[Unset, DatasourceConfig]):
        credential_overwrites (Union[Unset, DatasourceConfig]):
        page_size (Union[Unset, int]):
    """

    datasource_id: str
    prefix: str
    config_overwrites: Union[Unset, "DatasourceConfig"] = UNSET
    credential_overwrites: Union[Unset, "DatasourceConfig"] = UNSET
    page_size: Union[Unset, int] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        datasource_id = self.datasource_id

        prefix = self.prefix

        config_overwrites: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.config_overwrites, Unset):
            config_overwrites = self.config_overwrites.to_dict()

        credential_overwrites: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.credential_overwrites, Unset):
            credential_overwrites = self.credential_overwrites.to_dict()

        page_size = self.page_size

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "datasourceId": datasource_id,
                "prefix": prefix,
            }
        )
        if config_overwrites is not UNSET:
            field_dict["configOverwrites"] = config_overwrites
        if credential_overwrites is not UNSET:
            field_dict["credentialOverwrites"] = credential_overwrites
        if page_size is not UNSET:
            field_dict["page_size"] = page_size

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.datasource_config import DatasourceConfig

        d = src_dict.copy()
        datasource_id = d.pop("datasourceId")

        prefix = d.pop("prefix")

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

        page_size = d.pop("page_size", UNSET)

        list_request = cls(
            datasource_id=datasource_id,
            prefix=prefix,
            config_overwrites=config_overwrites,
            credential_overwrites=credential_overwrites,
            page_size=page_size,
        )

        list_request.additional_properties = d
        return list_request

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
