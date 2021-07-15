from collections.abc import Mapping, Set
from enum import Enum
from typing import Optional
import datetime
import uuid  # don't take too literally, these may be ObjectIds

import pandas as pd


class FeatureSetType(Enum):
    GENERIC = 1
    TRAINING = 2
    PREDICTION = 3
    GROUND_TRUTH = 4


class FeatureSetPermission(Enum):
    READ = 1
    WRITE = 2
    DELETE = 3


class FeatureSet:
    def __init__(
            self,
            id: uuid.UUID,
            version_number: int,
            name: str,
            description: str,
            type: FeatureSetType,
            creation_time: datetime.datetime,
            owner_id: str,
            acl: Mapping[str, Set[FeatureSetPermission]],
            metadata: Mapping[str, str],
            annotations: Mapping[str, str],
            archived: bool
    ):
        pass

    def create_version(
            self,
            df: pd.DataFrame,
            timestamp_column: str,
            independent_vars: [str] = [],
            target_vars: [str] = [],
            continuous_vars: [str] = [],
            categorical_vars: [str] = [],
            ordinal_vars: [str] = [],
            name: Optional[str] = None,
            description: Optional[str] = None,
            metadata: Mapping[str, str] = {},
            annotations: Mapping[str, str] = {}
    ) -> 'FeatureSetVersion':
        """Creates a new FeatureSetVersion"""
        pass

    def open_version(
            self,
            timestamp_column: str,
            independent_vars: [str] = [],
            target_vars: [str] = [],
            continuous_vars: [str] = [],
            categorical_vars: [str] = [],
            ordinal_vars: [str] = [],
            name: Optional[str] = None,
            description: Optional[str] = None,
            metadata: Mapping[str, str] = {},
            annotations: Mapping[str, str] = {}
    ) -> 'FeatureSetVersion':
        """Opens a FeatureSetVersion for writing"""
        pass

    def get_version(self, fsv_id: uuid.UUID) -> 'FeatureSetVersion':
        """Get FeatureSetVersion by id."""
        pass

    # TODO: paginated API
    def get_versions(self, offset: int, limit: int) -> ['FeatureSetVersion']:
        """Get all FeatureSetVersion for a FeatureSet."""
        pass

    # TODO: paginated API
    def get_versions_for_project(
            self,
            project_id: uuid.UUID,
            offset: int,
            limit: int
    ) -> ['FeatureSetVersion']:
        """Get all FeatureSetVersion for a FeatureSet."""
        pass

    def get_latest_version(self) -> 'FeatureSetVersion':
        """Get latest FeatureSetVersion of a FeatureSet."""
        pass

    def archive(self) -> None:
        """Archives FeatureSet"""
        pass

    def update_description(
            self,
            description: str
    ) -> None:
        """Updates a FeatureSet's annotations"""
        pass

    def update_featureset_annotations(
            self,
            annotations: Mapping[str, str]
    ) -> None:
        """Updates a FeatureSet's annotations"""
        pass

    def add_permission(self, user_id: str,
                       permissions: Set[str]) -> None:
        """Grant access to another user.

        Only the owner or domino administrators may modify permissions.
        """
        pass

    def drop_permission(self, user_id: str) -> None:
        """Drop all user permissions.

        Only the owner or domino administrators may modify permissions.
        """
        pass


class FeatureSetVersion:
    def __init__(
            self,
            fsv_id: uuid.UUID,
            fs_id: uuid.UUID,
            creation_time: datetime.datetime,
            url: str,
            timestamp_column: str,
            independent_vars: [str],
            target_vars: [str],
            continuous_vars: [str],
            categorical_vars: [str],
            ordinal_vars: [str],
            name: Optional[str],
            description: Optional[str],
            metadata: Mapping[str, str],
            annotations: Mapping[str, str],
            is_open: bool
    ):
        pass

    def delete(self) -> None:
        """Delete FeatureSetVersion record and data."""
        pass

    def get_df(self) -> pd.DataFrame:
        """Retrieve FeatureSetVersion data.

        Raises an exception if is_open=true
        """
        pass

    def append(self, df: pd.DataFrame) -> None:
        """Append a dataframe.

        Raises and exception if is_open=false
        """

    def close(self) -> None:
        """Closes a version.

        idempotent.
        """

class FeatureSetClient:
    def __init__(self):
        pass

    def create_featureset(
            self,
            name: str,                          # globally unique?
            type: FeatureSetType,
            description: Optional[str] = None,
            metadata: Mapping[str, str] = {},
            annotations: Mapping[str, str] = {}
    ) -> FeatureSet:
        """Registers a new FeatureSet with domino"""
        pass

    def get_featureset(self, fs_id: uuid.UUID) -> FeatureSet:
        """Get a FeatureSet"""
        pass

    def get_featureset_by_name(self, name: str) -> FeatureSet:
        """Get a FeatureSet"""
        pass

    def get_featuresets_for_project(
            self,
            project_id: uuid.UUID,
            type: FeatureSetType,
            offset: int = 0,
            limit: int = 1000
    ) -> [FeatureSet]:
        """Get FeatureSets containing a version created by a project"""
        pass


def client() -> FeatureSetClient:
    """Get client configured from environment variables"""
    pass
