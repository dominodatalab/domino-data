from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.training_set_filter_meta import TrainingSetFilterMeta


T = TypeVar("T", bound="TrainingSetFilter")


@_attrs_define
class TrainingSetFilter:
    """
    Attributes:
        project_id (str):
        meta (Union[Unset, TrainingSetFilterMeta]):
    """

    project_id: str
    meta: Union[Unset, "TrainingSetFilterMeta"] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        project_id = self.project_id

        meta: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.meta, Unset):
            meta = self.meta.to_dict()

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "projectId": project_id,
            }
        )
        if meta is not UNSET:
            field_dict["meta"] = meta

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.training_set_filter_meta import TrainingSetFilterMeta

        d = src_dict.copy()
        project_id = d.pop("projectId")

        _meta = d.pop("meta", UNSET)
        meta: Union[Unset, TrainingSetFilterMeta]
        if isinstance(_meta, Unset):
            meta = UNSET
        else:
            meta = TrainingSetFilterMeta.from_dict(_meta)

        training_set_filter = cls(
            project_id=project_id,
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
