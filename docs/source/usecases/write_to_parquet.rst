.. If there are any caveats/gotchas that users need to know, this and the API page should contian them.
   
Write to local file
===================

Parquet
-------

Because we use `PyArrow <https://arrow.apache.org/docs/python/>`_ to serialize and transport data, we can easily write the query result to a local parquet file. You can also use pandas as shown in the CSV example.

.. code-block:: python

   redshift = DataSourceClient().get_datasource("redshift-test")

   res = redshift.query("SELECT * FROM wines LIMIT 1000")

   # to_parquet() accepts a path or file-like object
   # the whole result is loaded and written once
   res.to_parquet("./wines_1000.parquet")


CSV
---

Because serializing to a CSV is lossy, we recommend using the `Pandas.to_csv <https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_csv.html#pandas-dataframe-to-csv>`_ API so you can leverage the multiple options that it provides.

.. code-block:: python
    
   redshift = DataSourceClient().get_datasource("redshift-test")

   res = redshift.query("SELECT * FROM wines LIMIT 1000")

   # See Pandas.to_csv documentation for all options
   csv_options = {header: True, quotechar: "'"}

   res.to_pandas().to_csv("./wines_1000.csv", **csv_options)
