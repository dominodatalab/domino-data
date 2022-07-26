from typing import Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="BatchSource")


@attr.s(auto_attribs=True)
class BatchSource:
    """
    Attributes:
        event_timestamp_column (Union[Unset, str]):
        created_timestamp_column (Union[Unset, str]):
        date_partition_column (Union[Unset, str]):
        database (Union[Unset, str]):
        query (Union[Unset, str]):
        table (Union[Unset, str]):
    """

    event_timestamp_column: Union[Unset, str] = UNSET
    created_timestamp_column: Union[Unset, str] = UNSET
    date_partition_column: Union[Unset, str] = UNSET
    database: Union[Unset, str] = UNSET
    query: Union[Unset, str] = UNSET
    table: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        event_timestamp_column = self.event_timestamp_column
        created_timestamp_column = self.created_timestamp_column
        date_partition_column = self.date_partition_column
        database = self.database
        query = self.query
        table = self.table

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if event_timestamp_column is not UNSET:
            field_dict["eventTimestampColumn"] = event_timestamp_column
        if created_timestamp_column is not UNSET:
            field_dict["createdTimestampColumn"] = created_timestamp_column
        if date_partition_column is not UNSET:
            field_dict["datePartitionColumn"] = date_partition_column
        if database is not UNSET:
            field_dict["database"] = database
        if query is not UNSET:
            field_dict["query"] = query
        if table is not UNSET:
            field_dict["table"] = table

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        event_timestamp_column = d.pop("eventTimestampColumn", UNSET)

        created_timestamp_column = d.pop("createdTimestampColumn", UNSET)

        date_partition_column = d.pop("datePartitionColumn", UNSET)

        database = d.pop("database", UNSET)

        query = d.pop("query", UNSET)

        table = d.pop("table", UNSET)

        batch_source = cls(
            event_timestamp_column=event_timestamp_column,
            created_timestamp_column=created_timestamp_column,
            date_partition_column=date_partition_column,
            database=database,
            query=query,
            table=table,
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
