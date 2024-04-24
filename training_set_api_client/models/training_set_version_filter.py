from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.training_set_version_filter_meta import TrainingSetVersionFilterMeta
    from ..models.training_set_version_filter_training_set_meta import (
        TrainingSetVersionFilterTrainingSetMeta,
    )


T = TypeVar("T", bound="TrainingSetVersionFilter")


@_attrs_define
class TrainingSetVersionFilter:
    """
    Attributes:
        project_id (str):
        training_set_meta (TrainingSetVersionFilterTrainingSetMeta):
        meta (TrainingSetVersionFilterMeta):
        training_set_name (Union[Unset, str]):
    """

    project_id: str
    training_set_meta: "TrainingSetVersionFilterTrainingSetMeta"
    meta: "TrainingSetVersionFilterMeta"
    training_set_name: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        project_id = self.project_id

        training_set_meta = self.training_set_meta.to_dict()

        meta = self.meta.to_dict()

        training_set_name = self.training_set_name

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "projectId": project_id,
                "trainingSetMeta": training_set_meta,
                "meta": meta,
            }
        )
        if training_set_name is not UNSET:
            field_dict["trainingSetName"] = training_set_name

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.training_set_version_filter_meta import TrainingSetVersionFilterMeta
        from ..models.training_set_version_filter_training_set_meta import (
            TrainingSetVersionFilterTrainingSetMeta,
        )

        d = src_dict.copy()
        project_id = d.pop("projectId")

        training_set_meta = TrainingSetVersionFilterTrainingSetMeta.from_dict(
            d.pop("trainingSetMeta")
        )

        meta = TrainingSetVersionFilterMeta.from_dict(d.pop("meta"))

        training_set_name = d.pop("trainingSetName", UNSET)

        training_set_version_filter = cls(
            project_id=project_id,
            training_set_meta=training_set_meta,
            meta=meta,
            training_set_name=training_set_name,
        )

        training_set_version_filter.additional_properties = d
        return training_set_version_filter

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
