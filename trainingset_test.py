#!/usr/bin/env python

from trainingset import client, model

import pandas as pd

tsv = client.create_training_set_version(
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

print(f"Created version: {tsv}")
print(f"Created version with trainingSetName: '{tsv.training_set_name}'")

tsv_by_num = client.get_training_set_version(tsv.training_set_name, tsv.number)

print(f"Got tsv by number: {tsv_by_num}")

assert dir(tsv_by_num) == dir(tsv)

ts = client.get_training_set(tsv.training_set_name)

print(f"Got training set: {ts}")

# XXX update featureset to add metadata

# search for metadata instead
found_ts = client.list_training_sets(
    filter=model.TrainingSetFilter(project_name="integration-test/quick-start")
)

print(f"Found training set: {found_ts}")
