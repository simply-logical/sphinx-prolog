# Copyright (C) 2021
# Author: Kacper Sokol <k.sokol@bristol.ac.uk>
# License: new BSD
"""
Implements a lexer for *pseudo Prolog* (`pProlog`) code block syntax
highlighting within Jupyter Book and Sphinx.

This implementation was inspired by:
* https://stackoverflow.com/questions/11413203/sphinx-pygments-lexer-filter-extension
* https://stackoverflow.com/questions/16469869/custom-syntax-highlighting-with-sphinx
* https://pygments.org/docs/lexerdevelopment/
* https://github.com/pygments/pygments/blob/master/pygments/lexers/prolog.py#L21
"""

import copy

from pygments.lexer import bygroups
from pygments.lexers import PrologLexer
from pygments.token import Name, Operator, Punctuation, String, Text

import sphinx_prolog

# namespace highlighting fix
_A = r'([a-z]+)(:)'
_A_SUB = (r'([a-z]+)(:)(?!-)' ,bygroups(Name.Namespace, Punctuation))
# overwrite function definition highlighting
_B_SUB_1 = (r'([a-z\u00c0-\u1fff\u3040-\ud7ff\ue000-\uffef]'
            r'[\w$\u00c0-\u1fff\u3040-\ud7ff\ue000-\uffef]*)'
            r'(\s*)(:-|-->)',
            bygroups(String.Atom, Text, Operator))
_B_SUB_2 = (r'([a-z\u00c0-\u1fff\u3040-\ud7ff\ue000-\uffef]'
            r'[\w$\u00c0-\u1fff\u3040-\ud7ff\ue000-\uffef]*)'
            r'(\s*)(\()',
            bygroups(String.Atom, Text, Punctuation))


#### pProlog Lexer ############################################################


class pPrologLexer(PrologLexer):
    """
    Defines *pseudo Prolog* (`pProlog`) lexer.

    This lexer allows to highlight pseudo Prolog code with::
       .. code-block:: pProlog

          my,pseudo,prolog;-code.
    """
    name = 'pProlog'
    aliases = ['pprolog']
    filenames = []
    mimetypes = ['text/x-pprolog']

    tokens = copy.deepcopy(PrologLexer.tokens)

    _a_i, _b_i_1, _b_i_2 = None, None, None
    for i, pattern in enumerate(tokens['root']):
        if pattern[0] == _A:
            _a_i = i
        if pattern[0] == _B_SUB_1[0]:
            _b_i_1 = i
        if pattern[0] == _B_SUB_2[0]:
            _b_i_2 = i
    assert _a_i is not None and _b_i_1 is not None and _b_i_2 is not None, (
        'The underlying Prolog lexer has been modified.')

    tokens['root'][_a_i] = _A_SUB
    tokens['root'][_b_i_1] = _B_SUB_1
    tokens['root'][_b_i_2] = _B_SUB_2


def setup(app):
    """
    Sets up the Sphinx extension for the *pseudo Prolog* (`pProlog`) lexer.
    """
    app.add_lexer('pProlog', pPrologLexer)  # startinline=True
    return {'version': sphinx_prolog.VERSION}
