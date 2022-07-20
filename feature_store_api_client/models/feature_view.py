from typing import Any, Dict, List, Type, TypeVar, Union

import datetime

import attr
from dateutil.parser import isoparse

from ..models.batch_source import BatchSource
from ..models.entity import Entity
from ..models.feature import Feature
from ..models.feature_view_tags import FeatureViewTags
from ..models.store_location import StoreLocation
from ..types import UNSET, Unset

T = TypeVar("T", bound="FeatureView")


@attr.s(auto_attribs=True)
class FeatureView:
    """
    Attributes:
        name (str):
        ttl (datetime.datetime):
        features (List[Feature]):
        batch_source (BatchSource):
        store_location (StoreLocation):
        entities (Union[Unset, List[Entity]]):
        tags (Union[Unset, FeatureViewTags]):
    """

    name: str
    ttl: datetime.datetime
    features: List[Feature]
    batch_source: BatchSource
    store_location: StoreLocation
    entities: Union[Unset, List[Entity]] = UNSET
    tags: Union[Unset, FeatureViewTags] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        name = self.name
        ttl = self.ttl.isoformat()

        features = []
        for features_item_data in self.features:
            features_item = features_item_data.to_dict()

            features.append(features_item)

        batch_source = self.batch_source.to_dict()

        store_location = self.store_location.to_dict()

        entities: Union[Unset, List[Dict[str, Any]]] = UNSET
        if not isinstance(self.entities, Unset):
            entities = []
            for entities_item_data in self.entities:
                entities_item = entities_item_data.to_dict()

                entities.append(entities_item)

        tags: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.tags, Unset):
            tags = self.tags.to_dict()

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "ttl": ttl,
                "features": features,
                "batchSource": batch_source,
                "storeLocation": store_location,
            }
        )
        if entities is not UNSET:
            field_dict["entities"] = entities
        if tags is not UNSET:
            field_dict["tags"] = tags

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        name = d.pop("name")

        ttl = isoparse(d.pop("ttl"))

        features = []
        _features = d.pop("features")
        for features_item_data in _features:
            features_item = Feature.from_dict(features_item_data)

            features.append(features_item)

        batch_source = BatchSource.from_dict(d.pop("batchSource"))

        store_location = StoreLocation.from_dict(d.pop("storeLocation"))

        entities = []
        _entities = d.pop("entities", UNSET)
        for entities_item_data in _entities or []:
            entities_item = Entity.from_dict(entities_item_data)

            entities.append(entities_item)

        _tags = d.pop("tags", UNSET)
        tags: Union[Unset, FeatureViewTags]
        if isinstance(_tags, Unset):
            tags = UNSET
        else:
            tags = FeatureViewTags.from_dict(_tags)

        feature_view = cls(
            name=name,
            ttl=ttl,
            features=features,
            batch_source=batch_source,
            store_location=store_location,
            entities=entities,
            tags=tags,
        )

        feature_view.additional_properties = d
        return feature_view

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
