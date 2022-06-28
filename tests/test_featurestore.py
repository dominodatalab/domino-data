"""TrainingSet tests."""

import datetime

import httpx
import numpy as np
import pandas as pd
import pytest

from domino_data import featurestore as fs


@pytest.mark.vcr
def test_create_feature_store(monkeypatch, respx_mock):
    """Client can create a FeatureStore."""

    monkeypatch.setenv("AWS_SHARED_CREDENTIALS_FILE", "tests/data/aws_credentials")
    mock_content = b"I am a blob"
    respx_mock.get("http://s3/url").mock(
        return_value=httpx.Response(200, content=mock_content),
    )
    features = [fs.Feature(name="total_trips_by_all_drivers", dtype="Int64")]

    batch_source = fs.BatchSource(
        name="driver_stats",
        data_source="SELECT * from driver_trips",
        event_timestamp_column="driver_column",
        created_timestamp_column="car_column",
        date_partition_column="driver_column",
    )

    bucket = "bucket-name"
    region = "us-west-2"

    store_location = fs.StoreLocation(bucket=bucket, region=region, resource_id="1234-id")

    project_id = "1234"
    feature_store_name = "driver_analysis"
    ttl = datetime.timedelta(seconds=86400 * 1)

    feature_views = [
        fs.FeatureView(
            name="driver_info",
            ttl=ttl,
            features=features,
            batch_source=batch_source,
            store_location=store_location,
        )
    ]

    client = fs.FeatureStoreClient()
    fs_response = client.post_feature_store(
        name=feature_store_name, feature_views=feature_views, bucket=bucket, region=region
    )

    assert fs_response.name == feature_store_name
    assert fs_response.project_id == project_id
    assert not fs_response.pending
