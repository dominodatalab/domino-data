from typing import Any, Dict, List, Type, TypeVar, Union

import attr

from ..models.training_set_filter_meta import TrainingSetFilterMeta
from ..types import UNSET, Unset

T = TypeVar("T", bound="TrainingSetFilter")


@attr.s(auto_attribs=True)
class TrainingSetFilter:
    """ """

    project_name: Union[Unset, str] = UNSET
    owner_name: Union[Unset, str] = UNSET
    meta: Union[Unset, TrainingSetFilterMeta] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        project_name = self.project_name
        owner_name = self.owner_name
        meta: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.meta, Unset):
            meta = self.meta.to_dict()

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if project_name is not UNSET:
            field_dict["projectName"] = project_name
        if owner_name is not UNSET:
            field_dict["ownerName"] = owner_name
        if meta is not UNSET:
            field_dict["meta"] = meta

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        project_name = d.pop("projectName", UNSET)

        owner_name = d.pop("ownerName", UNSET)

        _meta = d.pop("meta", UNSET)
        meta: Union[Unset, TrainingSetFilterMeta]
        if isinstance(_meta, Unset):
            meta = UNSET
        else:
            meta = TrainingSetFilterMeta.from_dict(_meta)

        training_set_filter = cls(
            project_name=project_name,
            owner_name=owner_name,
            meta=meta,
        )

        training_set_filter.additional_properties = d
        return training_set_filter

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
