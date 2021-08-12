#!/usr/bin/env python

from trainingset import client, models

client = client.client()

client.create_training_set_version(TrainingSetVersion(
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
))
