.. _custom-get_uctraining_set:
Retrieve TrainingSets
=====================


..
  The following line and the description of the get seem similar. 

Training sets may be fetched by version number or via a search.

Get TrainingSetVersion
----------------------

TrainingSetVersions may be retrieved by name and number.

.. code-block:: python

    tsv_by_num = TrainingSetClient.get_training_set_version(
        training_set_name="my-training-set",
        number=2,
    )

Raw data may be accessed:

.. code-block:: python

    raw_df = tsv_by_num.load_raw_pandas()

Training data may also be accessed:

.. code-block:: python

    training_df = tsv_by_num.load_training_pandas()


Find TrainingSetVersions
------------------------

..
  Is it correnct that get get a specifici training set version by name or number whereas find seraches for training set version based on specific criteria?

TrainingSetVersions for the current project my be searched by training set name, TrainingSet
metadata, and TrainingSetVersion metadata. Results matching all search fields will be returned.

.. code-block:: python

    versions = TrainingSetClient.list_training_set_versions(
        training_set_name="my-training-set",
        meta={"year": "2021"},
        training_set_meta={"category": "widgets"}
    )


Get TrainingSet
---------------

TrainingSets may be retrieved by name.

.. code-block:: python

   ts = TrainingSetClient.get_training_set("my-training-set")

Find TrainingSets
-----------------

TrainingSets may be searched for by metadata. Results matching all metadata fields will be returned.

.. code-block:: python

   ts = TrainingSetClient.list_training_sets(
       meta={"category": "widgets"},
   )
