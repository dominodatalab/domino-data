"""TrainingSet tests."""

import numpy as np
import pandas as pd
import pytest

from feature_store_api_client.api.default import post_feature_store_name
from feature_store_api_client.client import Client
from feature_store_api_client.models import (
    BatchSource,
    CreateFeatureStoreRequest,
    Entity,
    Feature,
    FeatureStore,
    FeatureView,
    FeatureViewTags,
    StoreLocation,
)


@pytest.mark.vcr
def test_create_feature_store():
    """Client can create a FeatureStore."""

    features = [Feature(name = "total_trips_by_all_drivers", value_type = "Int64")]

    batch_source = BatchSource(
        name = "driver_stats",
        data_source = "SELECT * from driver_trips",
        event_timestamp_column = "driver_column",
        created_timestamp_column = "car_column",
        date_partition_column = "driver_column",
    )

    store_location = StoreLocation(
        bucket = "bucket-name",
        region = "us-west-2"
    )

    project_id = "1234"
    feature_store_name = "driver_analysis"
    ttl = timedelta(seconds=86400 * 1)

    feature_views = [
        FeatureView(
            name = "driver_info",
            ttl = ttl,
            features = features,
            batch_source = batch_source,
            store_location = store_location
        )
    ]

    request = CreateFeatureStoreRequest(
        name = feature_store_name,
        project_id = project_id,
        feature_views = feature_views
    )

    fs = Client.post_feature_store_name(
        feature_store_name,
        self.client,
        request
    )

    assert fs.name == feature_store_name
    assert fs.project_id == project_id
    assert not fs.pending

