#!/usr/bin/env python

from trainingset import client, model

import pandas as pd

client.create_training_set_version(
    version=model.TrainingSetVersion(
        training_set="my-training-set",  # XXX should we restrict the set of characters that can be used?
        timestamp_column="ts",
        independent_vars=["foo"],
        target_vars=["bar"],
        continuous_vars=["baz"],
        categorical_vars=["asdf"],
        ordinal_vars=["xyz"],
        name="something",
        description="blah blah",
        metadata={},
    ),
    df=pd.DataFrame(),
    project_owner="integration-test",
    project_name="quick-start",
)
