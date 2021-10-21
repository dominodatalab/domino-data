Object store
============

Datasource type
---------------

The SDK supports object store type datasources (S3) and allows for easy retrieval and upload of objects. The following APIs are only available when using this type of datasource.


List
----

Get the datasource from the client:

.. code-block:: python

   from domino_data.datasource import Client

   s3_dev = Client().get_datasource("s3-dev")


You can list objects available in the datasource. You can also specify a prefix:

.. code-block:: python

   objects = s3_dev.list_objects()

   objects_under_path = s3_dev.list_objects("path_prefix")


Read
----

You can either use the API directly from the datasource entity:

.. code-block:: python

   # Get content as binary
   content = s3_dev.get("key")

   # Download content to file
   s3_dev.download_file("key", "./path/to/local/file")

   # Download content to file-like object
   f = io.BytesIO()
   s3_dev.download_fileobj("key", f)


Or from an object entity:

.. code-block:: python

   # Key object
   my_key = s3_dev.Object("key")

   # Get content as binary
   content = my_key.get()

   # Download content to file
   my_key.download_file("./path/to/local/file")

   # Download content to file-like object
   f = io.BytesIO()
   my_key.download_fileobj(f)


Write
-----


Similar APIs are available for writing data. From datasource:

.. code-block:: python

   # Put binary content to given object key
   s3_dev.put("key", b"content")

   # Upload file content to specified object key
   s3_dev.upload_file("key", "./path/to/local/file")

   # Upload file-like content to specified object key
   f = io.BytesIO(b"content")
   s3_dev.upload_fileobj("key", f)


As with read APIs, you can use those from the object entity.
