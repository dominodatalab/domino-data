from typing import Any, Dict, List, Type, TypeVar, cast

import datetime

import attr
from dateutil.parser import isoparse

from ..models.feature_store_offline_store_config import FeatureStoreOfflineStoreConfig
from ..models.git_provider_name import GitProviderName
from ..models.offline_store_type import OfflineStoreType

T = TypeVar("T", bound="FeatureStore")


@attr.s(auto_attribs=True)
class FeatureStore:
    """
    Attributes:
        id (str):
        owner_id (str):
        creation_time (datetime.datetime):
        offline_store_type (OfflineStoreType):
        offline_store_config (FeatureStoreOfflineStoreConfig):
        git_repo (str):
        git_service_provider (GitProviderName):
        project_ids (List[str]):
        last_updated_time (datetime.datetime):
    """

    id: str
    owner_id: str
    creation_time: datetime.datetime
    offline_store_type: OfflineStoreType
    offline_store_config: FeatureStoreOfflineStoreConfig
    git_repo: str
    git_service_provider: GitProviderName
    project_ids: List[str]
    last_updated_time: datetime.datetime
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        id = self.id
        owner_id = self.owner_id
        creation_time = self.creation_time.isoformat()

        offline_store_type = self.offline_store_type.value

        offline_store_config = self.offline_store_config.to_dict()

        git_repo = self.git_repo
        git_service_provider = self.git_service_provider.value

        project_ids = self.project_ids

        last_updated_time = self.last_updated_time.isoformat()

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "ownerId": owner_id,
                "creationTime": creation_time,
                "offlineStoreType": offline_store_type,
                "offlineStoreConfig": offline_store_config,
                "gitRepo": git_repo,
                "gitServiceProvider": git_service_provider,
                "projectIds": project_ids,
                "lastUpdatedTime": last_updated_time,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        id = d.pop("id")

        owner_id = d.pop("ownerId")

        creation_time = isoparse(d.pop("creationTime"))

        offline_store_type = OfflineStoreType(d.pop("offlineStoreType"))

        offline_store_config = FeatureStoreOfflineStoreConfig.from_dict(d.pop("offlineStoreConfig"))

        git_repo = d.pop("gitRepo")

        git_service_provider = GitProviderName(d.pop("gitServiceProvider"))

        project_ids = cast(List[str], d.pop("projectIds"))

        last_updated_time = isoparse(d.pop("lastUpdatedTime"))

        feature_store = cls(
            id=id,
            owner_id=owner_id,
            creation_time=creation_time,
            offline_store_type=offline_store_type,
            offline_store_config=offline_store_config,
            git_repo=git_repo,
            git_service_provider=git_service_provider,
            project_ids=project_ids,
            last_updated_time=last_updated_time,
        )

        feature_store.additional_properties = d
        return feature_store

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
