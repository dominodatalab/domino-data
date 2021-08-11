from typing import Any, Dict, List, Type, TypeVar

import attr

T = TypeVar("T", bound="TrainingSetVersionUrl")


@attr.s(auto_attribs=True)
class TrainingSetVersionUrl:
    """ """

    training_set_version_id: str
    url: str
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        training_set_version_id = self.training_set_version_id
        url = self.url

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "trainingSetVersionId": training_set_version_id,
                "url": url,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        training_set_version_id = d.pop("trainingSetVersionId")

        url = d.pop("url")

        training_set_version_url = cls(
            training_set_version_id=training_set_version_id,
            url=url,
        )

        training_set_version_url.additional_properties = d
        return training_set_version_url

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
