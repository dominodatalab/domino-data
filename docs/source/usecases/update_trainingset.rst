.. If there are any caveats/gotchas that users need to know, this and the API page should contian them.
   
.. _update_uctraining_set:

Update TrainingSets
===================

Metadata can be updated on both ``TrainingSet`` and ``TrainingSetVersion`` objects.

..
  Are there any other things to be aware of when updating the metadata? 

Update TrainingSet
------------------

The following example shows how to update your ``TrainingSet``:

.. code-block:: python

    ts = TrainingSetClient.get_training_set("my-training-set")

    ts.description = "widget transactions"
    ts.metadata.update({"region": "west"})

    updated = TrainingSetClient.update_training_set(ts)


Update TrainingSetVersion
-------------------------

The following example shows how to update your ``TrainingSetVersion``:

.. code-block:: python

    tsv = TrainingSetClient.get_training_set_version("my-training-set", 2)

    tsv.description = "2020 transactions"
    tsv.metadata.update({"status": "final"})

    updated = TrainingSetClient.update_training_set_version(tsv)
