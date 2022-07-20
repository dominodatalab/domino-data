from typing import Any, Dict, List, Type, TypeVar

import attr

T = TypeVar("T", bound="CreateFeatureStoreRequest")


@attr.s(auto_attribs=True)
class CreateFeatureStoreRequest:
    """
    Attributes:
        name (str):
        project_id (str):
        bucket (str):
        region (str):
        visible_credential (str):
        secret_credential (str):
    """

    name: str
    project_id: str
    bucket: str
    region: str
    visible_credential: str
    secret_credential: str
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        name = self.name
        project_id = self.project_id
        bucket = self.bucket
        region = self.region
        visible_credential = self.visible_credential
        secret_credential = self.secret_credential

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "projectId": project_id,
                "bucket": bucket,
                "region": region,
                "visibleCredential": visible_credential,
                "secretCredential": secret_credential,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        name = d.pop("name")

        project_id = d.pop("projectId")

        bucket = d.pop("bucket")

        region = d.pop("region")

        visible_credential = d.pop("visibleCredential")

        secret_credential = d.pop("secretCredential")

        create_feature_store_request = cls(
            name=name,
            project_id=project_id,
            bucket=bucket,
            region=region,
            visible_credential=visible_credential,
            secret_credential=secret_credential,
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
