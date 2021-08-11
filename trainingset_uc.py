#!/usr/bin/env python

from trainingset import client, models

client = client.client()

client.create_featureset(
    name="foo",
    project_id=
    kind=models.TrainingSetType.GENERIC,
    description="hippies",
    metadata={"foo": "bar"},
    annotations={"abc": "123"}
)
