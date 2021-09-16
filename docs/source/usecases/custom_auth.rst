.. _custom-auth:

Custom Authentication
=====================

Default
-------

Please refer to :ref:`auth` for the default behavior of the Client.


Usage
-----

To override the API key:

.. code-block:: python

   from domino_data_sdk.datasource import Client

   custom_api_key = "VALID_API_KEY"

   client = Client(api_key=custom_api_key)
   db = client.get_datasource("my-db")


To override the location of the token file:

.. code-block:: python

   from domino_data_sdk.datasource import Client

   custom_token_file = "/valid/token/file/location"

   client = Client(token_file=custom_token_file)
   db = client.get_datasource("my-db")
