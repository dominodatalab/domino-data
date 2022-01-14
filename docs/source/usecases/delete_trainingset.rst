.. _custom-delete_uctraining_set:
Delete TrainingSets
===================

..
  I think this section needs more information. Are there any other issued that need to be known before performing a delete operation. 

TrainingSets and TrainingSetVersions may be deleted.

Delete TrainingSetVersion
-------------------------

.. code-block:: python

    TrainingSetClient.delete_training_set_version("my-training-set", 2)

Delete TrainingSet
------------------

TrainingSets may only be deleted if they have no versions.

.. code-block:: python

    TrainingSetClient.delete_training_set("my-training-set")


To delete the TrainingSet and all versions:

.. code-block:: python

    found_tsvs = TrainingSetClient.list_training_set_versions(
        training_set_name="my-training-set",
    )

    for tsv in found_tsvs:
        TrainingSetClient.delete_training_set_version(tsv.training_set_name, tsv.number)

    TrainingSetClient.delete_training_set("my-training-set")
