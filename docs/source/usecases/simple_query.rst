Tabular store
=============

Setup
-----

First make sure the SDK is available in your workspace environment, see :ref:`install`.

Authentication
--------------
The Datasource client will use environment variables available in the workspace to automatically authenticate you.

To override this behavior, see :ref:`custom-auth`.

Usage
-----

Assuming a Datasource named *redshift-test* has been configured with valid credentials for the current user:

.. code-block:: python

   from domino_data.data_sources import DataSourceClient

   # instantiate a client and fetch the datasource instance
   redshift = DataSourceClient().get_datasource("redshift-test")

   query = """
        SELECT
            firstname,
            lastname,
            age
        FROM
            employees
        LIMIT 1000
    """

    # res is a simple wrapper of the query result
    res = redshift.query(query)
    # to_pandas() loads the result into a pandas dataframe
    df = res.to_pandas()
    # check the first 10 rows
    df.head(10)
