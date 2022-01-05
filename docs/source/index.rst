.. Domino Data API documentation master file, created by
   sphinx-quickstart on Thu Aug 26 10:10:16 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Domino Data API
===============

This Python library lets you access tabular and file-based data using consistent access patterns and SQL-based access to tabular data.  Using this method, there is no need to restart a workload to install drivers.  Connectors can be queried on the fly.  Results are available as dataframe abstractions for popular libraries.

In Domino 5.1, this new data access method is supported for Snowflake, Redshift, PostgreSQL, MySQL, and SQL Server and S3, with additional data sources planned for future releases.

In Domino 5.1, new data source support will be added for Google Cloud Storage.

.. NOTE:: This is a preview feature, not officially supported.


.. toctree::
   :caption: Getting Started
   :maxdepth: 2

   install
   auth

.. toctree::
   :caption: Datasource use cases
   :maxdepth: 1
   :glob:

   usecases/simple_query
   usecases/object_store
   usecases/write_to_parquet
   usecases/custom_auth
   usecases/config_override

.. toctree::
   :caption: TrainingSet use cases
   :maxdepth: 1
   :glob:

   usecases/create_trainingset
   usecases/get_trainingset
   usecases/update_trainingset
   usecases/delete_trainingset

Reference
=========

.. toctree::
   :caption: Modules
   :maxdepth: 2

   domino_data

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
