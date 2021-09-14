"""Training Set integration test"""

import pandas as pd
import pytest

from domino_data_sdk.trainingset import client, model


@pytest.mark.skip(reason="needs vcrpy integration")
def test_client():
    client.create_training_set_version(
        training_set_name="my-training-set",
        df=pd.DataFrame(),
        key_columns=["user_id", "transaction_id"],
        target_columns=["is_fraud"],
        exclude_columns=["extra_column1", "extra_column2"],
        monitoring_meta=model.MonitoringMeta(
            categorical_columns=["categorical_column1", "categorical_column2"],
        ),
        meta={"experiment_id": "123456"},
        project_name="integration-test/quick-start",
    )
