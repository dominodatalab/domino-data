from typing import Any, Dict, List, Type, TypeVar, Union

import datetime

import attr
from dateutil.parser import isoparse

from ..models.batch_source import BatchSource
from ..models.entity import Entity
from ..models.feature import Feature
from ..models.feature_view_dto_tags import FeatureViewDtoTags
from ..types import UNSET, Unset

T = TypeVar("T", bound="FeatureViewDto")


@attr.s(auto_attribs=True)
class FeatureViewDto:
    """
    Attributes:
        name (str):
        entities (List[Entity]):
        features (List[Feature]):
        batch_source (BatchSource):
        ttl (Union[Unset, datetime.datetime]):
        online (Union[Unset, bool]):
        tags (Union[Unset, FeatureViewDtoTags]):
    """

    name: str
    entities: List[Entity]
    features: List[Feature]
    batch_source: BatchSource
    ttl: Union[Unset, datetime.datetime] = UNSET
    online: Union[Unset, bool] = UNSET
    tags: Union[Unset, FeatureViewDtoTags] = UNSET
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

        batch_source = self.batch_source.to_dict()

        ttl: Union[Unset, str] = UNSET
        if not isinstance(self.ttl, Unset):
            ttl = self.ttl.isoformat()

        online = self.online
        tags: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.tags, Unset):
            tags = self.tags.to_dict()

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "entities": entities,
                "features": features,
                "batchSource": batch_source,
            }
        )
        if ttl is not UNSET:
            field_dict["ttl"] = ttl
        if online is not UNSET:
            field_dict["online"] = online
        if tags is not UNSET:
            field_dict["tags"] = tags

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

        batch_source = BatchSource.from_dict(d.pop("batchSource"))

        _ttl = d.pop("ttl", UNSET)
        ttl: Union[Unset, datetime.datetime]
        if isinstance(_ttl, Unset):
            ttl = UNSET
        else:
            ttl = isoparse(_ttl)

        online = d.pop("online", UNSET)

        _tags = d.pop("tags", UNSET)
        tags: Union[Unset, FeatureViewDtoTags]
        if isinstance(_tags, Unset):
            tags = UNSET
        else:
            tags = FeatureViewDtoTags.from_dict(_tags)

        feature_view_dto = cls(
            name=name,
            entities=entities,
            features=features,
            batch_source=batch_source,
            ttl=ttl,
            online=online,
            tags=tags,
        )

        feature_view_dto.additional_properties = d
        return feature_view_dto

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
