.. If there are any caveats/gotchas that users need to know, this and the API page should contian them.
   
.. _usecase-simple-query:

Tabular store
=============

Setup
-----

**Note:** Ensure that the SDK is available in your workspace environment, see :ref:`install` for setup information.

Authentication
--------------
The Datasource client uses environment variables available in the workspace to automatically authenticate your identity.

To override this behavior, see :ref:`custom-auth`.

Usage
-----

Assuming a Datasource named *redshift-test* has been configured with valid credentials for the current user:

.. code-block:: python

   from domino.data_sources import DataSourceClient

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
