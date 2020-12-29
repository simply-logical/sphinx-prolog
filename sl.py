# Copyright (C) 2020
# Author: Kacper Sokol <k.sokol@bristol.ac.uk>
# License: new BSD
"""
A Sphinx extension implementing `infobox`, `exercise`, `solution` and `swish`
directives used in the `online version <https://book.simply-logical.space/>`_
of the Simply Logical book.
This extension is compatible with and intended for Jupyter Book.

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


VERSION = '0.2'
__version__ = VERSION


def file_exists(file_path):
    """Checks whether a path exists and is a file."""
    if os.path.exists(file_path):
        if not os.path.isfile(file_path):
            raise RuntimeError('The code file ({}) is not a '
                               'file.'.format(file_path))
    else:
        raise RuntimeError('The code file ({}) does not '
                           'exist.'.format(file_path))
