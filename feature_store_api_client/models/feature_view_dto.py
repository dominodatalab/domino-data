from typing import Any, Dict, List, Type, TypeVar, Union, cast

import attr

from ..models.batch_source import BatchSource
from ..models.feature_view_dto_tags import FeatureViewDtoTags
from ..types import UNSET, Unset

T = TypeVar("T", bound="FeatureViewDto")


@attr.s(auto_attribs=True)
class FeatureViewDto:
    """
    Attributes:
        id (str):
        name (str):
        feature_store_id (str):
        entities (List[str]):
        features (List[str]):
        batch_source (BatchSource):
        ttl (Union[Unset, str]):
        online (Union[Unset, bool]):
        tags (Union[Unset, FeatureViewDtoTags]):
    """

    id: str
    name: str
    feature_store_id: str
    entities: List[str]
    features: List[str]
    batch_source: BatchSource
    ttl: Union[Unset, str] = UNSET
    online: Union[Unset, bool] = UNSET
    tags: Union[Unset, FeatureViewDtoTags] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        id = self.id
        name = self.name
        feature_store_id = self.feature_store_id
        entities = self.entities

        features = self.features

        batch_source = self.batch_source.to_dict()

        ttl = self.ttl
        online = self.online
        tags: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.tags, Unset):
            tags = self.tags.to_dict()

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "featureStoreId": feature_store_id,
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
        id = d.pop("id")

        name = d.pop("name")

        feature_store_id = d.pop("featureStoreId")

        entities = cast(List[str], d.pop("entities"))

        features = cast(List[str], d.pop("features"))

        batch_source = BatchSource.from_dict(d.pop("batchSource"))

        ttl = d.pop("ttl", UNSET)

        online = d.pop("online", UNSET)

        _tags = d.pop("tags", UNSET)
        tags: Union[Unset, FeatureViewDtoTags]
        if isinstance(_tags, Unset):
            tags = UNSET
        else:
            tags = FeatureViewDtoTags.from_dict(_tags)

        feature_view_dto = cls(
            id=id,
            name=name,
            feature_store_id=feature_store_id,
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
