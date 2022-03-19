from typing import Any, Dict, List, Type, TypeVar, Union

import attr

from ..models.feature_store import FeatureStore
from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateFeatureStoreRequest")


@attr.s(auto_attribs=True)
class CreateFeatureStoreRequest:
    """
    Attributes:
        name (str):
        project_id (str):
        feature_store (FeatureStore):
        description (Union[Unset, str]):
    """

    name: str
    project_id: str
    feature_store: FeatureStore
    description: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        name = self.name
        project_id = self.project_id
        feature_store = self.feature_store.to_dict()

        description = self.description

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "projectId": project_id,
                "featureStore": feature_store,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        name = d.pop("name")

        project_id = d.pop("projectId")

        feature_store = FeatureStore.from_dict(d.pop("featureStore"))

        description = d.pop("description", UNSET)

        create_feature_store_request = cls(
            name=name,
            project_id=project_id,
            feature_store=feature_store,
            description=description,
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
