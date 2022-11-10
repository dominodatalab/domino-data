from typing import Any, Dict, List, Type, TypeVar, Union, cast

import attr

from ..models.entity import Entity
from ..models.feature import Feature
from ..models.feature_view_tags import FeatureViewTags
from ..models.metadata import Metadata
from ..types import UNSET, Unset

T = TypeVar("T", bound="FeatureView")


@attr.s(auto_attribs=True)
class FeatureView:
    """
    Attributes:
        id (str):
        name (str):
        feature_store_id (str):
        metadata (Metadata):
        entities (List[Entity]):
        features (List[Feature]):
        tags (FeatureViewTags):
        project_ids (List[str]):
        ttl (Union[Unset, int]):
    """

    id: str
    name: str
    feature_store_id: str
    metadata: Metadata
    entities: List[Entity]
    features: List[Feature]
    tags: FeatureViewTags
    project_ids: List[str]
    ttl: Union[Unset, int] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        id = self.id
        name = self.name
        feature_store_id = self.feature_store_id
        metadata = self.metadata.to_dict()

        entities = []
        for entities_item_data in self.entities:
            entities_item = entities_item_data.to_dict()

            entities.append(entities_item)

        features = []
        for features_item_data in self.features:
            features_item = features_item_data.to_dict()

            features.append(features_item)

        tags = self.tags.to_dict()

        project_ids = self.project_ids

        ttl = self.ttl

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "featureStoreId": feature_store_id,
                "metadata": metadata,
                "entities": entities,
                "features": features,
                "tags": tags,
                "projectIds": project_ids,
            }
        )
        if ttl is not UNSET:
            field_dict["ttl"] = ttl

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        id = d.pop("id")

        name = d.pop("name")

        feature_store_id = d.pop("featureStoreId")

        metadata = Metadata.from_dict(d.pop("metadata"))

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

        tags = FeatureViewTags.from_dict(d.pop("tags"))

        project_ids = cast(List[str], d.pop("projectIds"))

        ttl = d.pop("ttl", UNSET)

        feature_view = cls(
            id=id,
            name=name,
            feature_store_id=feature_store_id,
            metadata=metadata,
            entities=entities,
            features=features,
            tags=tags,
            project_ids=project_ids,
            ttl=ttl,
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
