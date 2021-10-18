Create TrainingSets
===================

A TrainingSet is versioned set of data, column information, and other metadata. TrainingSets are
created implicitly when the first TrainingSetVersion with a particular ``training_set_name`` are added
using the ``create_training_set_version`` function.

A TrainingSet may only include versions from the same project. Attempting to add a version from a
different project will result in an error.

TrainingSet names must be strings containing only alphanumeric characters in the basic Latin
alphabet including dash and underscore: [-A-Za-z_]

.. code-block:: python

    training_set_version = client.create_training_set_version(
        training_set_name=training_set_name,
        df=my_df,
        key_columns=["user_id", "transaction_id"],
        target_columns=["is_fraud"],
        exclude_columns=["extra_column1", "extra_column2"],
        monitoring_meta=model.MonitoringMeta(
            timestamp_columns=["ts"],
            categorical_columns=["categorical_column1", "categorical_column2"],
            ordinal_columns=["ordinal_column1"],
        )
        meta={"year": "2021"}
    )
