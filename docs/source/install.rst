.. _install:

Install the Data SDK
====================

You can use the SDK by using the right Domino environment. If you want to install it manually with **pip** we highly recommand installing it as an extra dependency of the main `python domino package <https://github.com/dominodatalab/python-domino>`_.

Domino Standard Environment
---------------------------

The Data SDK comes pre-packaged in the `Domino Standard Environment (DSE) <https://docs.dominodatalab.com/en/5.0/reference/environments/Domino_4_standard_environments.html>`_ starting version 5.0.

If you want to use your own environment, you can easily install the SDK by adding the following to the *Dockefile Instructions* section:

.. code-block:: docker

   USER root

   ## Install Domino and Data SDK packages
   RUN python -m pip install dominodatalab[data]

   USER ubuntu

Python Package Index (PyPI)
---------------------------

.. note::
    If you use the SDK as a standalone library, the package name will be `domino_data`. We recommand installing it as part of the main domino package for easier and consistent import (see :ref:`usecase-simple-query` for an example)

.. code-block:: console

   $ python -m pip install dominodatalab[data]

If you only want the Data SDK, it is published in `PyPI <https://pypi.org/project/dominodatalab-data>`_:

.. code-block:: console

   $ python -m pip install dominodatalab-data


Releases
--------

Release history is available `here <https://pypi.org/project/dominodatalab-data/#history>`_.
