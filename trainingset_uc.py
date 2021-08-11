#!/usr/bin/env python

import trainingset.client as client

client = client.client()

client.create_featureset(
    name="foo",
    kind=client.TrainingSetType.GENERIC,
    description="hippies",
    metadata={"foo": "bar"},
    annotations={"abc": "123"}
)
