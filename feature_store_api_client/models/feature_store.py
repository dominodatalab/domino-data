from typing import Any, Dict, List, Type, TypeVar, Union

import datetime

import attr
from dateutil.parser import isoparse

from ..models.feature_view import FeatureView
from ..types import UNSET, Unset

T = TypeVar("T", bound="FeatureStore")


@attr.s(auto_attribs=True)
class FeatureStore:
    """
    Attributes:
        id (str):
        project_id (str):
        name (str):
        creation_time (datetime.datetime):
        feature_views (List[str]):
    """

    id: str
    project_id: str
    name: str
    creation_time: datetime.datetime
    feature_views: List[str]
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        id = self.id
        project_id = self.project_id
        name = self.name
        creation_time = self.creation_time.isoformat()
        feature_views = self.feature_views

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "projectId": project_id,
                "name": name,
                "creationTime": creation_time,
                "featureViews": feature_views,
            }
        )
        print(field_dict)

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        id = d.pop("id")

        project_id = d.pop("projectId")

        name = d.pop("name")

        creation_time = isoparse(d.pop("creationTime"))

        feature_view_ids = d.pop("featureViews")

        feature_store = cls(
            id=id,
            project_id=project_id,
            name=name,
            creation_time=creation_time,
            feature_views=feature_view_ids,
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
