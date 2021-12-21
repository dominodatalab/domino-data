Config Override
===============

Permanent vs local change
-------------------------

Datasource configuration are set in the Data/Datasource panel of the Domino UI. You can update it there for any permanent change.

Some configuration attributes can be overriden locally in the SDK. Each datasource type config is described in the section below (:ref:`configs`).

Usage
-----

You can create a config override with any of the config classes and update your datasource entity:

.. code-block:: python

   from domino.data_sources import DataSourceClient, SnowflakeConfig

   snowflake = DataSourceClient().get_datasource("snowflake-prod")

   # Build a override config with a different warehouse than configured in Domino
   config_xxl = SnowflakeConfig(warehouse="compute-xxl")

   # Local update with no permanent change
   snowflake.update(config=config_xxl)
   res = snowflake.query("SELECT COUNT(*) FROM very_large_table")

   # Override can also be used for temporary credentials
   snowflake.update(config=SnowflakeConfig(username="admin", password="<password>"))
   res = snowflake.query("SELECT secret_data FROM secret_table LIMIT 10")


To remove the config override, simply reset it:

.. code-block:: python

   from domino.data_sources import DataSourceClient, SnowflakeConfig

   snowflake = DataSourceClient().get_datasource("snowflake-prod")
   # Update to dev database
   snowflake.update(SnowflakeConfig(database="dev"))

   # Reset to default values
   snowflake.reset_config()
   res = snowflake.query("SELECT * FROM prod_table")


.. _configs:

Classes
-------

.. currentmodule:: domino_data.data_sources

Redshift
^^^^^^^^

.. autoclass:: RedshiftConfig
   :members:
   :undoc-members:
   :noindex:

PostgreSQL
^^^^^^^^^^

.. autoclass:: PostgreSQLConfig
  :members:
  :undoc-members:
  :noindex:

Snowflake
^^^^^^^^^

.. autoclass:: SnowflakeConfig
   :members:
   :undoc-members:
   :noindex:

S3
^^

.. autoclass:: S3Config
   :members:
   :undoc-members:
   :noindex:
