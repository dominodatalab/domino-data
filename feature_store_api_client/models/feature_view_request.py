from typing import Any, Dict, List, Type, TypeVar, Union

import attr

from ..models.entity import Entity
from ..models.feature import Feature
from ..models.feature_view_request_tags import FeatureViewRequestTags
from ..types import UNSET, Unset

T = TypeVar("T", bound="FeatureViewRequest")


@attr.s(auto_attribs=True)
class FeatureViewRequest:
    """
    Attributes:
        name (str):
        entities (List[Entity]):
        features (List[Feature]):
        tags (FeatureViewRequestTags):
        ttl (Union[Unset, int]):
    """

    name: str
    entities: List[Entity]
    features: List[Feature]
    tags: FeatureViewRequestTags
    ttl: Union[Unset, int] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        name = self.name
        entities = []
        for entities_item_data in self.entities:
            entities_item = entities_item_data.to_dict()

            entities.append(entities_item)

        features = []
        for features_item_data in self.features:
            features_item = features_item_data.to_dict()

            features.append(features_item)

        tags = self.tags.to_dict()

        ttl = self.ttl

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "entities": entities,
                "features": features,
                "tags": tags,
            }
        )
        if ttl is not UNSET:
            field_dict["ttl"] = ttl

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        name = d.pop("name")

        entities = []
        _entities = d.pop("entities")
        for entities_item_data in _entities:
            entities_item = Entity.from_dict(entities_item_data)

            entities.append(entities_item)

        features = []
        _features = d.pop("features")
        for features_item_data in _features:
            features_item = Feature.from_dict(features_item_data)

            features.append(features_item)

        tags = FeatureViewRequestTags.from_dict(d.pop("tags"))

        ttl = d.pop("ttl", UNSET)

        feature_view_request = cls(
            name=name,
            entities=entities,
            features=features,
            tags=tags,
            ttl=ttl,
        )

        feature_view_request.additional_properties = d
        return feature_view_request

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
