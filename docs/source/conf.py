# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
from typing import List

import os
import sys

sys.path.insert(0, os.path.abspath("../../domino_data"))


# -- Project information -----------------------------------------------------

project = "Domino Data API"
copyright = "2021, Aaron Read, Gabriel Haim"
author = "Aaron Read, Gabriel Haim"


# -- General configuration ---------------------------------------------------

# Sphinx enabled extensions
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx_rtd_theme",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns: List[str] = []

# Enable type hints
autodoc_typehints = "both"
autodoc_typehints_format = "short"

# -- Options for HTML output -------------------------------------------------

# Theme for documentation uses ReadTheDocs plugin
html_theme = "sphinx_rtd_theme"

# Napoleon config
napoleon_google_docstring = True
