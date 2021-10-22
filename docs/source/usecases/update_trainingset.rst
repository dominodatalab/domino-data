Update TrainingSets
===================

Metadata may be updated on both TrainingSet and TrainingSetVersion objects.

Update TrainingSet
------------------

.. code-block:: python

    ts = client.get_training_set("my-training-set")

    ts.description = "widget transactions"
    ts.metadata.update({"region": "west"})

    updated = client.update_training_set(ts)


Update TrainingSetVersion
-------------------------

.. code-block:: python

    tsv = client.get_training_set_version("my-training-set", 2)

    tsv.description = "2020 transactions"
    tsv.metadata.update({"status": "final"})

    updated = client.update_training_set_version(tsv)
