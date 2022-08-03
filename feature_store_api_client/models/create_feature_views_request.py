from typing import Any, Dict, List, Type, TypeVar

import attr

from ..models.feature_view import FeatureView

T = TypeVar("T", bound="CreateFeatureViewsRequest")


@attr.s(auto_attribs=True)
class CreateFeatureViewsRequest:
    """
    Attributes:
        name (str):
        feature_views (List[FeatureView]):
    """

    name: str
    feature_views: List[FeatureView]
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        name = self.name
        feature_views = []
        for feature_views_item_data in self.feature_views:
            feature_views_item = feature_views_item_data.to_dict()

            feature_views.append(feature_views_item)

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "featureViews": feature_views,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        name = d.pop("name")

        feature_views = []
        _feature_views = d.pop("featureViews")
        for feature_views_item_data in _feature_views:
            feature_views_item = FeatureView.from_dict(feature_views_item_data)

            feature_views.append(feature_views_item)

        create_feature_views_request = cls(
            name=name,
            feature_views=feature_views,
        )

        create_feature_views_request.additional_properties = d
        return create_feature_views_request

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
