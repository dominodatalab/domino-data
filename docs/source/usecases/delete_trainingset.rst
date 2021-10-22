Delete TrainingSets
===================

TrainingSets and TrainingSetVersions may be deleted.

Delete TrainingSetVersion
-------------------------

.. code-block:: python

    client.delete_training_set_version("my-training-set", 2)

Delete TrainingSet
------------------

TrainingSets may only be deleted if they have no versions.

.. code-block:: python

    client.delete_training_set("my-training-set")


To delete the TrainingSet and all versions:

.. code-block:: python

    found_tsvs = client.list_training_set_versions(
        training_set_name="my-training-set",
    )

    for tsv in found_tsvs:
        client.delete_training_set_version(tsv.training_set_name, tsv.number)

    client.delete_training_set("my-training-set")
