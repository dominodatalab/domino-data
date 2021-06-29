from collections.abc import Mapping, Set
from enum import Enum
import datetime
import uuid

import pandas as pd


# Sample Usage
#
# import featureset
#
# client = featureset.client()
#
# fs = client.create_featureset("my featureset", metadata={"some": "immutable data"},
#                               annotations={"useful": "mutable data"})
#
# df = data_science()
#
# client.create_version(df, fs.id, timestamp_columns=['timestamp'],
#                       key_columns=['foo'], result_columns=['bar', 'baz'],
#                       metadata={}, annotations={})

class FeatureSetPermission(Enum):
    READ = 1
    WRITE = 2
    DELETE = 3


class FeatureSet:
    def __init__(self, fs_id: uuid.UUID,
                 creation_time: datetime.datetime,
                 owner_id: str,
                 acl: Mapping[str, Set[FeatureSetPermission]],
                 description: str,
                 metadata: Mapping[str, str],
                 annotations: Mapping[str, str],
                 archived: bool):
        self.id = id
        self.creation_time = creation_time
        self.owner_id = owner_id
        self.acl = acl
        self.description = description
        self.metadata = metadata        # immutable
        self.annotations = annotations  # mutable, for usability
        self.archived = archived


class FeatureSetVersion:
    def __init__(self, fsv_id: uuid.UUID,
                 fs_id: uuid.UUID,
                 creation_time: datetime.datetime,
                 url: str,
                 datatype: str,
                 encoding: str,
                 timestamp_columns: [str],
                 key_columns: [str],
                 result_columns: [str],
                 metadata: Mapping[str, str],
                 annotations: Mapping[str, str],
                 pending: bool):
        self.id = id
        self.fs_id = fs_id
        self.url = url
        self.datatype = datatype        # if this is all collunmar, maybe not needed yet
        self.encoding = encoding        # for internal use (e.g. parquet, etc)
        self.timestamp_columns = key_columns
        self.key_columns = key_columns
        self.result_columns = result_columns
        self.metadata = metadata        # immutable
        self.annotations = annotations  # mutable
        self.pending = pending


class FeatureSetClient:
    def __init__(self, bucket):
        self.bucket = bucket

    def create_featureset(self, description: str, metadata: Mapping[str, str],
                          annotations: Mapping[str, str]) -> FeatureSet:
        """Registers a new FeatureSet with domino"""
        pass

    def get_featureset(self, fs_id: uuid.UUID) -> FeatureSet:
        """Get a FeatureSet"""
        pass

    def archive_featureset(self, fs_id: uuid.UUID) -> FeatureSet:
        """Archives FeatureSet"""
        pass

    def update_featureset_description(
            self,
            fs_id: uuid.UUID,
            description: str
    ) -> FeatureSet:
        """Updates a FeatureSet's annotations"""
        pass

    def update_featureset_annotations(
            self,
            fs_id: uuid.UUID,
            annotations: Mapping[str, str]
    ) -> FeatureSet:
        """Updates a FeatureSet's annotations"""
        pass

    def add_permission(self, user_id: str,
                       permissions: Set[str]) -> FeatureSet:
        """Grant access to another user.

        Only the owner or domino administrators may modify permissions.
        """
        pass

    def drop_permission(self, user_id: str) -> FeatureSet:
        """Drop all user permissions.

        Only the owner or domino administrators may modify permissions.
        """
        pass

    def create_version(self, df: pd.DataFrame,
                       fs_id: uuid.UUID,
                       timestamp_columns: [str],
                       key_columns: [str],
                       result_columns: [str],
                       metadata: Mapping[str, str],
                       annotations: Mapping[str, str]) -> FeatureSetVersion:
        try:
            fsv = self._reg_pending_upload(fs_id, timestamp_columns,
                                           key_columns, result_columns,
                                           metadata, annotations)

            df.to_parquet(fsv.url)

            return self._reg_completed_upload(fsv.id)
        except Exception as exn:
            self._reg_failed_upload()
            raise exn

    def get_version(self, fsv_id: uuid.UUID) -> FeatureSetVersion:
        """Get FeatureSetVersion by id."""
        pass

    def get_versions(self, fs_id: uuid.UUID) -> [FeatureSetVersion]:
        """Get all FeatureSetVersion for a FeatureSet."""
        pass

    def get_latest_version(self, fs_id: uuid.UUID) -> FeatureSetVersion:
        """Get latest FeatureSetVersion of a FeatureSet."""
        pass

    def delete_version(self, fsv_id: uuid.UUID) -> FeatureSetVersion:
        """Delete FeatureSetVersion record and data."""
        pass

    def get_df(self, fsv_id: uuid.UUID) -> pd.DataFrame:
        """Retrieve FeatureSetVersion data."""

        fsv = self.get_version(id)

        df = pd.read_parquet(fsv.url)

        return df

    def _reg_pending_upload(
            self,
            fs_id: uuid.UUID,
            timestamp_columns: [str],
            key_columns: [str],
            result_columns: [str],
            metadata: Mapping[str, str],
            annotations: Mapping[str, str]
    ) -> FeatureSetVersion:
        """Register beginning of FeatureSetVersion upload with metadata service.

        Server will return a pending FeatureSetVersion.
        """

        pass

    def _reg_completed_upload(self, fsv_id: str) -> FeatureSetVersion:
        """Register completion of a FeatureSetVersion upload with metadata service.

        Server will remove pending flag from FeatureSetVersion.
        """
        pass

    def _reg_failed_upload(self, fsv_id: str) -> FeatureSetVersion:
        """Register failure of a FeatureSetVersion upload.

        Server deletes FeatureSetVersion or marks it as deleted.
        """
        pass


def client() -> FeatureSetClient:
    """Get client configured from environment variables"""
    pass
