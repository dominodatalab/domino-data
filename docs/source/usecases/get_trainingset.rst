.. _get_uctraining_set:

Retrieve TrainingSets
=====================


..
  The following line and the description of the get seem similar. 

You can get `TrainingSets` using their version number or using an explicit search.

Get TrainingSetVersion
----------------------

`TrainingSetVersions` can be retrieved by name and number.

.. code-block:: python

    tsv_by_num = TrainingSetClient.get_training_set_version(
        training_set_name="my-training-set",
        number=2,
    )

You can also access the raw data from the `TrainingSetVersion`.

.. code-block:: python

    raw_df = tsv_by_num.load_raw_pandas()

Training data can also be accessed.

.. code-block:: python

    training_df = tsv_by_num.load_training_pandas()


Find TrainingSetVersions
------------------------

..
  Is it correnct that get gets a specifici training set version by name or number whereas find seraches for training set version based on specific criteria?

You can search for `TrainingSetVersions` for the current project using the training set name, `TrainingSet` metadata, and `TrainingSetVersion` metadata. Results matching all search fields are returned.

.. code-block:: python

    versions = TrainingSetClient.list_training_set_versions(
        training_set_name="my-training-set",
        meta={"year": "2021"},
        training_set_meta={"category": "widgets"}
    )


Get TrainingSet
---------------

You can retrieve `TrainingSets` by name.

.. code-block:: python

   ts = TrainingSetClient.get_training_set("my-training-set")

Find TrainingSets
-----------------

You can serach `TrainingSets` by metadata. Results matching all metadata fields are returned.

.. code-block:: python

   ts = TrainingSetClient.list_training_sets(
       meta={"category": "widgets"},
   )
