from typing import Any, Dict, List, Type, TypeVar

import attr

T = TypeVar("T", bound="StoreLocation")


@attr.s(auto_attribs=True)
class StoreLocation:
    """
    Attributes:
        bucket (str):
        region (str):
        resource_id (str):
    """

    bucket: str
    region: str
    resource_id: str
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        bucket = self.bucket
        region = self.region
        resource_id = self.resource_id

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({"bucket": bucket, "region": region, "resourceId": resource_id})

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        bucket = d.pop("bucket")

        region = d.pop("region")

        resource_id = d.pop("resourceId")

        store_location = cls(bucket=bucket, region=region, resource_id=resourceId)

        store_location.additional_properties = d
        return store_location

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
