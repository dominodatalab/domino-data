from typing import Any, Dict, List, Type, TypeVar

import attr

from ..models.feature_view_request import FeatureViewRequest

T = TypeVar("T", bound="UpsertFeatureViewsRequest")


@attr.s(auto_attribs=True)
class UpsertFeatureViewsRequest:
    """
    Attributes:
        feature_views (List[FeatureViewRequest]):
        git_commit_hash (str):
    """

    feature_views: List[FeatureViewRequest]
    git_commit_hash: str
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        feature_views = []
        for feature_views_item_data in self.feature_views:
            feature_views_item = feature_views_item_data.to_dict()

            feature_views.append(feature_views_item)

        git_commit_hash = self.git_commit_hash

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "featureViews": feature_views,
                "gitCommitHash": git_commit_hash,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        feature_views = []
        _feature_views = d.pop("featureViews")
        for feature_views_item_data in _feature_views:
            feature_views_item = FeatureViewRequest.from_dict(feature_views_item_data)

            feature_views.append(feature_views_item)

        git_commit_hash = d.pop("gitCommitHash")

        upsert_feature_views_request = cls(
            feature_views=feature_views,
            git_commit_hash=git_commit_hash,
        )

        upsert_feature_views_request.additional_properties = d
        return upsert_feature_views_request

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
