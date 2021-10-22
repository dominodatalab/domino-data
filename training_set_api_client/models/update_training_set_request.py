from typing import Any, Dict, List, Type, TypeVar, Union

import attr

from ..models.update_training_set_request_meta import UpdateTrainingSetRequestMeta
from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateTrainingSetRequest")


@attr.s(auto_attribs=True)
class UpdateTrainingSetRequest:
    """ """

    meta: UpdateTrainingSetRequestMeta
    description: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        meta = self.meta.to_dict()

        description = self.description

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "meta": meta,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        meta = UpdateTrainingSetRequestMeta.from_dict(d.pop("meta"))

        description = d.pop("description", UNSET)

        update_training_set_request = cls(
            meta=meta,
            description=description,
        )

        update_training_set_request.additional_properties = d
        return update_training_set_request

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
