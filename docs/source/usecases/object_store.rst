.. If there are any caveats/gotchas that users need to know, this and the API page should contian them.

Object store
============

Datasource type
---------------

The SDK supports object store type datasources (S3) and allows for easy retrieval and upload of objects. **Note:** The following APIs are only available when using this type of datasource.


List
----

Get the datasource from the client:

.. code-block:: python

   from domino.data_sources import DataSourceClient

   s3_dev = DataSourceClient().get_datasource("s3-dev")


You can list objects available in the datasource. You can also specify a prefix:

.. code-block:: python

   objects = s3_dev.list_objects()

   objects_under_path = s3_dev.list_objects("path_prefix")


Read
----

You can get object content, without having to create object entities, by using the datasource API and specifying the ``Object`` key name:

.. code-block:: python

   # Get content as binary
   content = s3_dev.get("key")

   # Download content to file
   s3_dev.download_file("key", "./path/to/local/file")

   # Download content to file-like object
   f = io.BytesIO()
   s3_dev.download_fileobj("key", f)


You can also get the datasource entity content from an object entity:

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


Similar to the read/get APIs, you can also write data to a specific object key. From the datasource:

.. code-block:: python

   # Put binary content to given object key
   s3_dev.put("key", b"content")

   # Upload file content to specified object key
   s3_dev.upload_file("key", "./path/to/local/file")

   # Upload file-like content to specified object key
   f = io.BytesIO(b"content")
   s3_dev.upload_fileobj("key", f)


.. I cerated this code example for putting a file object, this NEEDS to really be checked.   

You can also write from the object entity.

.. code-block:: python

   # Key object
   my_key = s3_dev.Object("key")

   # Put content as binary
   my_key.put(b"content")

   # Upload content from file
   my_key.upload_file("./path/to/local/file")

   # Upload content from file-like object
   f = io.BytesIO()
   my_key.upload_fileobj(f)


