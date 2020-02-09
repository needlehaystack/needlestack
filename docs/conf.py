# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# http://www.sphinx-doc.org/en/master/config

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
sys.path.insert(0, os.path.abspath('..'))


# -- Compile Protobufs -------------------------------------------------------

# Protobufs are not precompiled and need to be generated at Sphinx runtime.
# This is a hack and should be made into an extension.
import pkg_resources
from glob import glob
from grpc_tools import protoc

_proto_include = pkg_resources.resource_filename('grpc_tools', '_proto')
_project_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
_status_code = protoc.main(
    [
        f"-I{_project_dir}",
        f"--python_out={_project_dir}",
        f"--grpc_python_out={_project_dir}",
        *glob(f"{_project_dir}/needlestack/apis/*.proto"),
        f"-I{_proto_include}",
        f"--proto_path={_proto_include}",
        f"--proto_path={_project_dir}",
    ]
)


# -- Project information -----------------------------------------------------

project = 'Needlestack'
copyright = '2019, Cung Tran'
author = 'Cung Tran'
version = "0.1.0-rc0"
release = version


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.autosectionlabel',
    'sphinxcontrib.napoleon',
    'sphinx_autodoc_typehints'
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']
