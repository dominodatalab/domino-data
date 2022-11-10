from typing import Any, Dict, List, Type, TypeVar

import attr

from ..models.create_feature_store_request_offline_store_config import (
    CreateFeatureStoreRequestOfflineStoreConfig,
)
from ..models.git_provider_name import GitProviderName
from ..models.offline_store_type import OfflineStoreType

T = TypeVar("T", bound="CreateFeatureStoreRequest")


@attr.s(auto_attribs=True)
class CreateFeatureStoreRequest:
    """
    Attributes:
        name (str):
        offline_store_type (OfflineStoreType):
        offline_store_config (CreateFeatureStoreRequestOfflineStoreConfig):
        git_repo (str):
        git_service_provider (GitProviderName):
    """

    name: str
    offline_store_type: OfflineStoreType
    offline_store_config: CreateFeatureStoreRequestOfflineStoreConfig
    git_repo: str
    git_service_provider: GitProviderName
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        name = self.name
        offline_store_type = self.offline_store_type.value

        offline_store_config = self.offline_store_config.to_dict()

        git_repo = self.git_repo
        git_service_provider = self.git_service_provider.value

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "offlineStoreType": offline_store_type,
                "offlineStoreConfig": offline_store_config,
                "gitRepo": git_repo,
                "gitServiceProvider": git_service_provider,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        name = d.pop("name")

        offline_store_type = OfflineStoreType(d.pop("offlineStoreType"))

        offline_store_config = CreateFeatureStoreRequestOfflineStoreConfig.from_dict(
            d.pop("offlineStoreConfig")
        )

        git_repo = d.pop("gitRepo")

        git_service_provider = GitProviderName(d.pop("gitServiceProvider"))

        create_feature_store_request = cls(
            name=name,
            offline_store_type=offline_store_type,
            offline_store_config=offline_store_config,
            git_repo=git_repo,
            git_service_provider=git_service_provider,
        )

        create_feature_store_request.additional_properties = d
        return create_feature_store_request

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
