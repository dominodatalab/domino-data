from typing import Any, Dict, List, Type, TypeVar

import attr

from ..models.feature_store_sync_result import FeatureStoreSyncResult

T = TypeVar("T", bound="UnlockFeatureStoreRequest")


@attr.s(auto_attribs=True)
class UnlockFeatureStoreRequest:
    """
    Attributes:
        feature_store_id (str):
        sync_result (FeatureStoreSyncResult):
    """

    feature_store_id: str
    sync_result: FeatureStoreSyncResult
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        feature_store_id = self.feature_store_id
        sync_result = self.sync_result.value

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "featureStoreId": feature_store_id,
                "syncResult": sync_result,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        feature_store_id = d.pop("featureStoreId")

        sync_result = FeatureStoreSyncResult(d.pop("syncResult"))

        unlock_feature_store_request = cls(
            feature_store_id=feature_store_id,
            sync_result=sync_result,
        )

        unlock_feature_store_request.additional_properties = d
        return unlock_feature_store_request

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
