from typing import Any, Dict, List, Type, TypeVar

import attr

T = TypeVar("T", bound="BatchSource")


@attr.s(auto_attribs=True)
class BatchSource:
    """
    Attributes:
        name (str):
        data_source (str):
        event_timestamp_column (str):
        created_timestamp_column (str):
        date_partition_column (str):
    """

    name: str
    data_source: str
    event_timestamp_column: str
    created_timestamp_column: str
    date_partition_column: str
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        data_source = self.data_source
        event_timestamp_column = self.event_timestamp_column
        created_timestamp_column = self.created_timestamp_column
        date_partition_column = self.date_partition_column

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "dataSource": data_source,
                "eventTimestampColumn": event_timestamp_column,
                "createdTimestampColumn": created_timestamp_column,
                "datePartitionColumn": date_partition_column,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        data_source = d.pop("dataSource")

        event_timestamp_column = d.pop("eventTimestampColumn")

        created_timestamp_column = d.pop("createdTimestampColumn")

        date_partition_column = d.pop("datePartitionColumn")

        batch_source = cls(
            data_source=data_source,
            event_timestamp_column=event_timestamp_column,
            created_timestamp_column=created_timestamp_column,
            date_partition_column=date_partition_column,
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
