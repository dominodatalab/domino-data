from typing import Any, Dict, List, Type, TypeVar

import attr

from ..models.batch_source_source_options import BatchSourceSourceOptions

T = TypeVar("T", bound="BatchSource")


@attr.s(auto_attribs=True)
class BatchSource:
    """
    Attributes:
        data_source_type (str):
        event_timestamp_column (str):
        created_timestamp_column (str):
        source_options (BatchSourceSourceOptions):
    """

    data_source_type: str
    event_timestamp_column: str
    created_timestamp_column: str
    source_options: BatchSourceSourceOptions
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        data_source_type = self.data_source_type
        event_timestamp_column = self.event_timestamp_column
        created_timestamp_column = self.created_timestamp_column
        source_options = self.source_options.to_dict()

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "dataSourceType": data_source_type,
                "eventTimestampColumn": event_timestamp_column,
                "createdTimestampColumn": created_timestamp_column,
                "sourceOptions": source_options,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        data_source_type = d.pop("dataSourceType")

        event_timestamp_column = d.pop("eventTimestampColumn")

        created_timestamp_column = d.pop("createdTimestampColumn")

        source_options = BatchSourceSourceOptions.from_dict(d.pop("sourceOptions"))

        batch_source = cls(
            data_source_type=data_source_type,
            event_timestamp_column=event_timestamp_column,
            created_timestamp_column=created_timestamp_column,
            source_options=source_options,
        )

        batch_source.additional_properties = d
        return batch_source

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
