from typing import Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="LockFeatureStoreRequest")


@attr.s(auto_attribs=True)
class LockFeatureStoreRequest:
    """
    Attributes:
        feature_store_id (str):
        project_name (Union[Unset, str]):
        user_name (Union[Unset, str]):
        run_id (Union[Unset, str]):
    """

    feature_store_id: str
    project_name: Union[Unset, str] = UNSET
    user_name: Union[Unset, str] = UNSET
    run_id: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        feature_store_id = self.feature_store_id
        project_name = self.project_name
        user_name = self.user_name
        run_id = self.run_id

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "featureStoreId": feature_store_id,
            }
        )
        if project_name is not UNSET:
            field_dict["projectName"] = project_name
        if user_name is not UNSET:
            field_dict["userName"] = user_name
        if run_id is not UNSET:
            field_dict["runId"] = run_id

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        feature_store_id = d.pop("featureStoreId")

        project_name = d.pop("projectName", UNSET)

        user_name = d.pop("userName", UNSET)

        run_id = d.pop("runId", UNSET)

        lock_feature_store_request = cls(
            feature_store_id=feature_store_id,
            project_name=project_name,
            user_name=user_name,
            run_id=run_id,
        )

        lock_feature_store_request.additional_properties = d
        return lock_feature_store_request

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
