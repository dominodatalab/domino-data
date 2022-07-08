from typing import Any, Dict, List, Type, TypeVar, Union

import attr

from ..models.feature_store import FeatureStore
from ..models.feature_view import FeatureView
from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateFeatureStoreRequest")


@attr.s(auto_attribs=True)
class CreateFeatureStoreRequest:
    """
    Attributes:
        name (str):
        project_id (str):
        datasource_id (str):
        feature_views (List[FeatureView]):
    """

    name: str
    project_id: str
    datasource_id: str
    feature_views: List[FeatureView]
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        name = self.name
        project_id = self.project_id
        datasource_id = self.datasource_id

        feature_views = []
        _feature_views = d.pop("featureViews")
        for fv in _feature_views:
            f = FeatureView.to_dict(fv)

            feature_views.append(f)

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "projectId": project_id,
                "datasourceId": datasource_id,
                "featureViews": feature_views,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        name = d.pop("name")

        project_id = d.pop("projectId")
        datasource_id = d.pop("datasourceId")

        feature_Views = []
        _feature_views = d.pop("featureViews")
        for fv in _feature_views:
            f = FeatureView.from_dict(fv)

            feature_views.append(f)

        create_feature_store_request = cls(
            name=name,
            project_id=project_id,
            feature_views=feature_views,
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
