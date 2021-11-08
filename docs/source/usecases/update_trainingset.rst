Update TrainingSets
===================

Metadata may be updated on both TrainingSet and TrainingSetVersion objects.

Update TrainingSet
------------------

.. code-block:: python

    ts = TrainingSetClient.get_training_set("my-training-set")

    ts.description = "widget transactions"
    ts.metadata.update({"region": "west"})

    updated = TrainingSetClient.update_training_set(ts)


Update TrainingSetVersion
-------------------------

.. code-block:: python

    tsv = TrainingSetClient.get_training_set_version("my-training-set", 2)

    tsv.description = "2020 transactions"
    tsv.metadata.update({"status": "final"})

    updated = TrainingSetClient.update_training_set_version(tsv)
