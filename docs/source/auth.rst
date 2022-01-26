.. If there are any caveats/gotchas that users need to know, this and the API page should contian them.
   
.. _auth:

Authentication
==============

Methods
-------

Using the SDK there are two methods available for authentication:

* **Credential propagation:** A token is periodically refreshed and stored in a file. The file location is defined in the **DOMINO_TOKEN_FILE** env variable

* **API Key:** If enabled, the user API key is exported in the **DOMINO_USER_API_KEY** env variable


Availability
------------

**Note:** Those methods are not available in all run types. The following table lists the availability for these methods. 


+---------------+---------+-------+---------+
| Run type      | Who?    | Token | Api Key |
+===============+=========+=======+=========+
| Workspace     | Creator | Yes   | Yes     |
+---------------+---------+-------+---------+
| Job           | Creator | Yes   | Yes     |
+---------------+---------+-------+---------+
| Scheduled Job | Creator | Yes   | Yes     |
+---------------+---------+-------+---------+
| Launcher      | User    | Yes   | Yes     |
+---------------+---------+-------+---------+
| App           | Creator | Yes   | Yes     |
+---------------+---------+-------+---------+
| Model API     | N/A     | No    | No      |
+---------------+---------+-------+---------+

.. warning::
   As described in the matrix, Model API does not support automatic authentication.

   You must follow the instructions in the :ref:`custom-auth` section to use the `DataSourceClient` or the `TrainingSetClient` in this type of run.
