.. _create_uctraining_set:

Create TrainingSets
===================

A TrainingSet is versioned set of data, column information, and other metadata. TrainingSets are
created implicitly when the first TrainingSetVersion with a particular ``training_set_name`` are added
using the ``create_training_set_version`` function.

A TrainingSet may only include versions from the same project. Attempting to add a version from a
different project will result in an error.

TrainingSet names must be strings containing only alphanumeric characters in the basic Latin
alphabet including dash and underscore: ``[-A-Za-z_-]``

.. code-block:: python

    from domino.training_sets import TrainingSetClient, model

    training_set_version = TrainingSetClient.create_training_set_version(
        training_set_name=training_set_name,
        df=my_pandas_dataframe,
        key_columns=["user_id", "transaction_id"],
        target_columns=["is_fraud"],
        exclude_columns=["extra_column1", "extra_column2"],
        monitoring_meta=model.MonitoringMeta(
            timestamp_columns=["ts"],
            categorical_columns=["categorical_column1", "categorical_column2"],
            ordinal_columns=["ordinal_column1"],
        ),
        meta={"year": "2021"}
    )

Note that you are unable to use a TrainingSet for model monitoring unless you providing a value for
the ``monitoring_meta`` keyword argument. You can still create a TrainingSet without this argument,
but TrainingSets created without the ``monitoring_meta`` keyword argument cannot be used for model
monitoring. If you select a Training Set created without the ``monitoring_meta`` keyword
argument while trying to register a Model API for monitoring from the Monitoring tab of the page
for that Model API, then you will see the error ``The selected Feature Set Version cannot currently be used for
monitoring because it does not contain a schema definition.``
