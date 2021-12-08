.. _custom-auth:

Custom Authentication
=====================

Default
-------

Please refer to :ref:`auth` for the default behavior of the DataSourceClient and TrainingSetClient.


Datasources
-----------

To override the API key:

.. code-block:: python

   from domino.data_sources import DataSourceClient

   custom_api_key = "VALID_API_KEY"

   client = DataSourceClient(api_key=custom_api_key)
   db = client.get_datasource("my-db")


To override the location of the token file:

.. code-block:: python

   from domino.data_sources import DataSourceClient

   custom_token_file = "/valid/token/file/location"

   client = DataSourceClient(token_file=custom_token_file)
   db = client.get_datasource("my-db")


Training Sets
-------------

The training set client is a python module wrapping a set of API methods. To override authentication, you need to set the right environment variable with your own user API key.

Python
^^^^^^

.. code-block:: python

   import os

   os.environ["DOMINO_USER_API_KEY"] = "<your-own-api-key>"

   # In model API if the client version is <0.1.8
   os.environ["DOMINO_API_HOST"] = os.getenv("DOMINO_USER_HOST")

Shell
^^^^^

.. code-block:: shell

   export DOMINO_USER_API_KEY=<your-own-api-key>

   # In model API if the client version is <0.1.8
   export DOMINO_API_HOST=$DOMINO_USER_HOST
