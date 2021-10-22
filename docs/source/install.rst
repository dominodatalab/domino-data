.. _install:

Install the Data SDK
====================

You can use the SDK by using the right Domino environment or by installing it with **pip**.

Domino Standard Environment
---------------------------

The Data SDK comes pre-packaged in the `Domino Standard Environment (DSE) <https://docs.dominodatalab.com/en/5.0/reference/environments/Domino_4_standard_environments.html>`_ starting version 5.0.

If you want to use your own environment, you can easily install the SDK by adding the following to the *Dockefile Instructions* section:

.. code-block:: docker

   ## Install Domino Data SDK
   RUN pip install --user dominodatalab-data

Python Package Index (PyPI)
---------------------------

The SDK is published in `PyPI <https://pypi.org/project/dominodatalab-data>`_ and you can install it directly with pip:

.. code-block:: console

   $ python -m pip install dominodatalab-data


Releases
--------

Release history is available `here <https://pypi.org/project/dominodatalab-data/#history>`_.
