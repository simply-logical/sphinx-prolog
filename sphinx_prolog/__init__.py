# Copyright (C) 2020
# Author: Kacper Sokol <k.sokol@bristol.ac.uk>
# License: new BSD
"""
A Sphinx extension implementing `pProlog` syntax highlighting and `infobox`,
`exercise`, `solution` and `swish` directives used to author Prolog-infused
interactive online resources.
This extension is compatible with, and intended for, Jupyter Book.

See `this tutorial <https://www.sphinx-doc.org/en/master/development/tutorials/todo.html>`_
for more details on building custom directives.
`This <http://www.xavierdupre.fr/blog/2015-06-07_nojs.html>`_ blog post is also
useful.
`docutils`' nodes description is available
`here <https://docutils.sourceforge.io/docs/ref/doctree.html>`_, and their
documentation `here <http://code.nabla.net/doc/docutils/api/docutils/nodes/>`_.

There are two lists of 3rd party extension that can be used as a reference:
`awesome-sphinxdoc <https://github.com/yoloseem/awesome-sphinxdoc>`_ and
`sphinx extension survey <https://sphinxext-survey.readthedocs.io/>`_.
The `sphinxcontrib-proof <https://framagit.org/spalax/sphinxcontrib-proof/>`_
extension was particularly useful for developing the `exercise` directive.
"""

import os

VERSION = '0.4.post1'
__version__ = VERSION

_STATIC_PATH = os.path.join(os.path.dirname(__file__), '_static')


def file_exists(file_path, file_type='code'):
    """Checks whether a path exists and is a file."""
    if os.path.exists(file_path):
        if not os.path.isfile(file_path):
            raise RuntimeError('The {} file ({}) is not a '
                               'file.'.format(file_type, file_path))
    else:
        raise RuntimeError('The {} file ({}) does not '
                           'exist.'.format(file_type, file_path))


def get_static_path(filename):
    """Returns a full path to a static extension file."""
    file_path = os.path.join(_STATIC_PATH, filename)
    # file_exists(file_path, file_type='static')
    if not os.path.exists(file_path):
        raise RuntimeError('The static path ({}) does not '
                           'exist.'.format(file_path))
    return file_path


def is_css_registered(app, filename):
    """
    Checks whether a given css file has been added to the Sphinx register.
    """
    for css_file, _ in app.registry.css_files:
        if filename == css_file:
            return True
    return False


def is_js_registered(app, filename):
    """
    Checks whether a given js file has been added to the Sphinx register.
    """
    for js_file, _ in app.registry.js_files:
        if filename == js_file:
            return True
    return False


def include_static_path(app):
    """
    Includes the contents of the `_static` directory distributed with this
    extension.
    (Should be attached to the `builder-inited` Sphinx event.)

    In addition to the `html_static_path` loading path, Sphinx also uses
    `html_extra_path`.
    This variable can be accessed via:

    * `self.state.document.settings.env.config.html_static_path`
      for directives and
    * `self.document.settings.env.config.html_static_path` for nodes.

    `html_static_path is relative to `self.document.settings.env.app.confdir`,
    and the build directory can be obtained from
    `document.settings.env.app.builder.outdir`.

    Alternatively, files can be copied manually by attaching a dedicated
    function to the `build-finished` Sphinx event::

       from sphinx.util.fileutil import copy_asset

       def copy_asset_files(app, exc):
           asset_files = [...]
           if exc is None:  # build succeeded
               for path in asset_files:
                   copy_asset(path, os.path.join(app.outdir, '_static'))

    See here for more details: https://github.com/sphinx-doc/sphinx/issues/1379
    """
    if _STATIC_PATH not in app.config.html_static_path:
        app.config.html_static_path.append(_STATIC_PATH)
