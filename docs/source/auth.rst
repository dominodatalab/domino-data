.. _auth:

Authentication
==============

Methods
-------

The SDK uses one of two available methods for authentication:

* Credential propagation: a token is periodically refreshed and stored in a file whose location is defined in the **DOMINO_TOKEN_FILE** env variable

* API Key: If enabled, the user API key is injected in the **DOMINO_USER_API_KEY** env variable


Availability
------------

Those two methods are not available in all run types. Follow the following matrix for availability:

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
