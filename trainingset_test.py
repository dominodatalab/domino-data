#!/usr/bin/env python

from trainingset import client, model

import pandas as pd

client.create_training_set_version(
    training_set_name="my-training-set",
    df=pd.DataFrame(),
    key_columns=["user_id", "transaction_id"],
    target_columns=["is_fraud"],
    exclude_columns=["extra_column1", "extra_column2"],
    monitoring_meta={
        "categorical_columns": ["categorical_column1", "categorical_column2"],
    },
    meta={
        "experiment_id": "123456"
    },
    project_name="integration-test/quick-start",
)
