# Copyright (C) 2020
# Author: Kacper Sokol <k.sokol@bristol.ac.uk>
# License: new BSD
"""
Implements the `swish` directive for Jupyter Book and Sphinx.
"""

import glob
import os
import re
import sphinx.util.osutil
import sys

from docutils import nodes
from docutils.parsers.rst import Directive, directives

import sphinx_prolog

STATIC_CSS_FILES = ['sphinx-prolog.css', 'lpn.css', 'jquery-ui.min.css']
STATIC_JS_FILES = ['lpn.js', 'jquery-ui.min.js']
STATIC_FILES = (STATIC_CSS_FILES + STATIC_JS_FILES
                + ['lpn/lpn-run.png', 'lpn/lpn-close.png'])

if sys.version_info >= (3, 0):
    unicode = str

_EXAMPLES_RGX = '\s*^/\*\*\s*<examples>\s*$.*?(?!^\*/\s*$).*?^\*/\s*$\s*'
EXAMPLES_PATTERN = re.compile(_EXAMPLES_RGX, flags=(re.M | re.I | re.S))
_LABEL_RGX = '<(swishq:\S+)>'
LABEL_PATTERN = re.compile(_LABEL_RGX, flags=(re.M | re.I | re.S))
_LABEL_STRING_RGX = '(?:^.+<)(\S+)(?:>\s*$)'
LABEL_STRING_PATTERN = re.compile(_LABEL_STRING_RGX, flags=(re.M | re.I | re.S))
_HIDE_EXAMPLES_RGX = ('$\s*^\s*<span class="cm">\s*/\*\*\s*&lt;examples&gt;\s*'
                      '</span>.*?<span class="cm">\s*\*/\s*</span>')
HIDE_EXAMPLES_PATTERN = re.compile(
    _HIDE_EXAMPLES_RGX, flags=(re.M | re.I | re.S))

PROLOG_TEMP_DIR = 'src/code/temp'
PROLOG_OUT_DIR = '_sources/prolog_build_files'
PROLOG_SUFFIX = '-merged.pl'


#### SWISH directive ##########################################################


class swish_box(nodes.General, nodes.Element):
    """A `docutils` node holding Simply Logical swish boxes."""


def visit_swish_box_node(self, node):
    """Builds an opening HTML tag for Simply Logical swish boxes."""
    inline = node.attributes.get('inline', False)
    inline_tag = 'span' if inline else 'div'

    lang = node.attributes.get('language')
    if lang is None:
        cls = 'extract swish'
    else:
        # ensure Prolog syntax highlighting
        assert lang == 'Prolog', 'SWISH query blocks must be Prolog syntax'
        # support Prolog code syntax highlighting -> the `highlight` class
        cls = 'extract swish highlight highlight-{} notranslate'.format(lang)

    self.body.append(self.starttag(node, inline_tag, CLASS=cls))


def depart_swish_box_node(self, node):
    """Builds a closing HTML tag for Simply Logical swish boxes."""
    inline = node.attributes.get('inline', False)
    # lack of `\n` after the `span` tag ensures correct spacing of the text
    inline_tag = '</span>' if inline else '</div>\n'

    self.body.append(inline_tag)


def visit_swish_box_node_(self, node):
    """
    Builds a prefix for embedding Simply Logical swish boxes in LaTeX and raw
    text.
    """
    raise NotImplemented


def depart_swish_box_node_(self, node):
    """
    Builds a postfix for embedding Simply Logical swish boxes in LaTeX and raw
    text.
    """
    raise NotImplemented


class swish_code(nodes.literal_block, nodes.Element):
    """
    A `docutils` node holding the **code** embedded in the Simply Logical swish
    boxes.
    """


def visit_swish_code_node(self, node):
    """Builds an opening HTML tag for Simply Logical swish **code** boxes."""
    env = self.document.settings.env

    attributes = {}
    class_list = ['literal-block', 'source', 'swish']

    # get node id
    node_ids = node.get('ids', [])
    assert len(node_ids) == 1
    assert node_ids[0].startswith('swish')
    assert node_ids[0].endswith('-code')
    #
    swish_label = node.get('label', None)
    assert swish_label is not None
    assert node_ids[0] == '{}-code'.format(nodes.make_id(swish_label))

    lang = node.attributes.get('language')
    # ensure Prolog syntax highlighting
    assert lang == 'Prolog', 'SWISH query blocks must be Prolog syntax'

    # get user-provided SWISH queries if present (`query-text` HTML attribute)
    query_text = node.attributes.get('query_text', None)
    if query_text is not None:
        attributes['query-text'] = query_text

    # get user-provided SWISH query id if present (`query-id` HTML attribute)
    query_id = node.attributes.get('query_id', None)
    if query_id is not None:
        # ensure that all of the referenced queries are also in this
        # document as otherwise the inheritance JavaScript will not work
        if not hasattr(env, 'sl_swish_query'):
            raise RuntimeError('A swish query box with *{}* id has not '
                               'been found.'.format(query_id))
        iid = []
        for i_ in query_id.strip().split(' '):
            i = i_.strip()
            if not i:
                continue
            if env.sl_swish_query[i] not in self.docnames:
                raise RuntimeError(
                    ('The code block *{}* placed in *{}* document uses query '
                     '*{}*, which is in a different document (*{}*). '
                     'Query referencing only works in a scope of a single '
                     'document.'.format(swish_label, self.docnames, i,
                                        env.sl_swish_query[i]))
                )
            iid.append('{}-query'.format(nodes.make_id(i)))
        attributes['query-id'] = ' '.join(iid)

    # composes the `inherit-id` HTML attribute if present
    inherit_id = node.attributes.get('inherit_id', None)
    if inherit_id is not None:
        iid = []
        for i_ in inherit_id.strip().split(' '):
            i = i_.strip()
            if not i:
                continue
            iid.append('{}-code'.format(nodes.make_id(i)))
            # ensure that all of the inherited code blocks are also in this
            # document as otherwise the inheritance JavaScript will not work
            assert hasattr(env, 'sl_swish_code')
            if env.sl_swish_code[i]['main_doc'] not in self.docnames:
                raise RuntimeError(
                    ('The code block *{}* placed in *{}* document inherits '
                     '*{}*, which is in a different document (*{}*). '
                     'Inheritance only works in a scope of a single '
                     'document.'.format(swish_label, self.docnames, i,
                                        env.sl_swish_code[i]['main_doc']))
                )
        attributes['inherit-id'] = ' '.join(iid)
        # if the code block inherits from another, it needs a special class
        class_list.append('inherit')

    # composes the `source-text-start` HTML attribute if present
    source_text_start = node.attributes.get('source_text_start', None)
    if source_text_start is not None:
        attributes['source-text-start'] = source_text_start

    # composes the `source-text-end` HTML attribute if present
    source_text_end = node.attributes.get('source_text_end', None)
    if source_text_end is not None:
        attributes['source-text-end'] = source_text_end

    # compose the `prolog_file` HTML attribute if present
    prolog_file = node.attributes.get('prolog_file', None)
    if prolog_file is not None:
        attributes['prolog-file'] = prolog_file

    # if the block is being inherited from, it needs a special class
    if swish_label in env.sl_swish_inherited:
        class_list.append('temp')

    # If either of the `source-text-start` or `source-text-end` attributes are
    # present, call a modified version of the `starttag` method/function that
    # does not prune whitespaces (such as newline characters) from the content
    # of the attributes.
    # This is achieved by modifying the call to `attval` (towards the end of
    # the implementation) with a substitute function (not removing
    # whitespace characters) that is also ported to this file.
    if 'source-text-start' in attributes or 'source-text-end' in attributes:
        # escape html such as <, >, ", etc. but **preserve new lines**
        tag = starttag(self, node, 'pre',  # suffix='',
                       CLASS=' '.join(class_list),
                       **attributes)
    else:
        tag = self.starttag(node, 'pre',  # suffix='',
                            CLASS=' '.join(class_list),
                            **attributes)
    #self.body.append(tag)
    #self.visit_literal_block(node)

    highlighted = self.highlighter.highlight_block(
        node.rawsource, lang, location=node)
    # strip the external `<div class="highlight"><pre>` and `</pre></div>` tags
    # (the existing swish extract syntax has been adapted)
    assert highlighted.startswith('<div class="highlight"><pre>')
    highlighted = highlighted[28:]
    assert highlighted.endswith('</pre></div>\n')
    highlighted = highlighted[:-13]

    # hide the examples block
    hide_examples_global = env.config.sp_swish_hide_examples
    assert isinstance(hide_examples_global, bool)
    assert 'hide_examples' in node.attributes
    hide_examples_local = node.attributes['hide_examples']
    assert isinstance(hide_examples_local, bool) or hide_examples_local is None
    if hide_examples_global and hide_examples_local in (None, True):
        hide_examples = True
    elif hide_examples_global and hide_examples_local is False:
        hide_examples = False
    elif not hide_examples_global and hide_examples_local:
        hide_examples = True
    elif not hide_examples_global and hide_examples_local in (None, False):
        hide_examples = False
    else:
        assert False
    # hide each occurrence of the examples block
    if hide_examples:
        highlighted = HIDE_EXAMPLES_PATTERN.sub(
            lambda x: '<div class="hide-examples">{}</div>'.format(x.group(0)),
            highlighted)

    self.body.append(tag + highlighted)

    self.body.append('</pre>')
    # otherwise the raw content is inserted and
    # the `depart_swish_query_node` method is executed
    # (see the depart_swish_code_node method for more details)
    raise nodes.SkipNode


def starttag(self, node, tagname, suffix='\n', empty=False, **attributes):
    """
    Construct and return a start tag given a node (id & class attributes
    are extracted), tag name, and optional attributes.

    Ported from https://docutils.sourceforge.io/docutils/writers/_html_base.py
    with a tweaked `attval` call towards the end.
    """
    tagname = tagname.lower()
    prefix = []
    atts = {}
    ids = []
    for (name, value) in attributes.items():
        atts[name.lower()] = value
    classes = []
    languages = []
    # unify class arguments and move language specification
    for cls in node.get('classes', []) + atts.pop('class', '').split():
        if cls.startswith('language-'):
            languages.append(cls[9:])
        elif cls.strip() and cls not in classes:
            classes.append(cls)
    if languages:
        # attribute name is 'lang' in XHTML 1.0 but 'xml:lang' in 1.1
        atts[self.lang_attribute] = languages[0]
    if classes:
        atts['class'] = ' '.join(classes)
    assert 'id' not in atts
    ids.extend(node.get('ids', []))
    if 'ids' in atts:
        ids.extend(atts['ids'])
        del atts['ids']
    if ids:
        atts['id'] = ids[0]
        for id in ids[1:]:
            # Add empty "span" elements for additional IDs. Note
            # that we cannot use empty "a" elements because there
            # may be targets inside of references, but nested "a"
            # elements aren't allowed in XHTML (even if they do
            # not all have a "href" attribute).
            if empty or isinstance(node,
                        (nodes.bullet_list, nodes.docinfo,
                         nodes.definition_list, nodes.enumerated_list,
                         nodes.field_list, nodes.option_list,
                         nodes.table)):
                # Insert target right in front of element.
                prefix.append('<span id="%s"></span>' % id)
            else:
                # Non-empty tag.  Place the auxiliary <span> tag
                # *inside* the element, as the first child.
                suffix += '<span id="%s"></span>' % id
    attlist = sorted(atts.items())
    parts = [tagname]
    for name, value in attlist:
        # value=None was used for boolean attributes without
        # value, but this isn't supported by XHTML.
        assert value is not None
        if isinstance(value, list):
            values = [unicode(v) for v in value]
            # the modified call to the `attval` function/method
            parts.append('%s="%s"' % (name.lower(),
                                      attval(self, ' '.join(values))))
        else:
            # the modified call to the `attval` function/method
            parts.append('%s="%s"' % (name.lower(),
                                      attval(self, unicode(value))))
    if empty:
        infix = ' /'
    else:
        infix = ''
    return ''.join(prefix) + '<%s%s>' % (' '.join(parts), infix) + suffix


def attval(self, text):
    """
    Cleanse, HTML encode, and return attribute value text.

    Ported from https://docutils.sourceforge.io/docutils/writers/_html_base.py
    and tweaked to preserve *whitespaces* -- such as *newline* characters --
    in the content of HTML attributes.
    (Needed for `source-text-start` and `source-text-end' attributes of the
    swish code boxes, which contain raw Prolog code.)
    """
    encoded = self.encode(text)
    if self.in_mailto and self.settings.cloak_email_addresses:
        # Cloak at-signs ("%40") and periods with HTML entities.
        encoded = encoded.replace('%40', '&#37;&#52;&#48;')
        encoded = encoded.replace('.', '&#46;')
    return encoded


def depart_swish_code_node(self, node):
    """Builds a closing HTML tag for Simply Logical swish **code** boxes."""
    self.depart_literal_block(node)


def visit_swish_code_node_(self, node):
    """
    Builds a prefix for embedding Simply Logical swish **code** boxes in LaTeX
    and raw text.
    """
    raise NotImplemented


def depart_swish_code_node_(self, node):
    """
    Builds a postfix for embedding Simply Logical swish **code** boxes in LaTeX
    and raw text.
    """
    raise NotImplemented


def strip_examples_block(text):
    """
    Strips the *examples* block of text from the input text::
       file content
       file content
       ...
       /** <examples>
       content that will be stripped
       content that will be stripped
       ...
       content that will be stripped
       */
    resulting in::
       file content
       file content
       ...
    """
    no_examples = EXAMPLES_PATTERN.sub('\n', text).strip()
    return no_examples


class SWISH(Directive):
    """
    Defines the `swish` directive for building Simply Logical swish boxes with
    code.
    The `swish` directive is of the form::
       .. swish:: swish:1.2.3 (required)
          :query-text: ?-linked(a,b,X). ?-linked(X,a,Y). (optional)
          :inherit-id: swish:4.1.1 [swish:4.1.2 swish:4.1.3] (optional)
          :source-text-start: 4.1.1-start (optional)
          :source-text-end: 4.1.1-end (optional)
          :hide-examples: false
          :build-file: false

    All of the ids need to be Prolog code files **with** the `swish:` prefix
    and **without the** `.pl` **extension**, located in a single directory.
    The directory is provided to Sphinx via the `sp_code_directory` config
    setting and is **required**.

    Optionally, the `sp_swish_url` config setting can be provided, which
    specifies the URL of the execution swish server. If one is not given,
    the default URL hardcoded in the swish JavaScript library will be used
    (i.e., `https://swish.swi-prolog.org/`).

    Optionally, `sp_swish_hide_examples` can globally toggle the visibility of
    the *example* blocks in SWISH code blocks.

    If any of the code blocks uses `build-file` set to `true`,
    the `sp_swish_book_url` config setting must be provided.

    This directive operates on three Sphinx environmental variables:

    sl_swish_code
      A dictionary encoding the association between code files and documents.
      See the description of the `memorise_code` method for more details.

    sl_has_swish
      A set of names of documents that include swish boxes.

    sl_swish_inherited
      A dictionary of code ids that are being inherited by swish boxes.
      The value for each code id is a set of documents that included the
      inheritance.

    This Sphinx extension monitors the code files for changes and
    regenerates the content pages that use them if a change is detected.
    """
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = False
    has_content = True
    option_spec = {'query-text': directives.unchanged,
                   'query-id': directives.unchanged,
                   'inherit-id': directives.unchanged,
                   'source-text-start': directives.unchanged,
                   'source-text-end': directives.unchanged,
                   'hide-examples': directives.unchanged,
                   'build-file': directives.unchanged}

    def run(self):
        """Builds a swish box."""
        # NOTE: using `env.note_dependency()` may simplify monitoring for code
        #       file changes.
        env = self.state.document.settings.env
        options = self.options

        # memorise that this document (a content source file) uses at least
        # one swish box
        if not hasattr(env, 'sl_has_swish'):
            env.sl_has_swish = set()
        if env.docname not in env.sl_has_swish:
            env.sl_has_swish.add(env.docname)

        # retrieve the path to the directory holding the code files
        sp_code_directory = env.config.sp_code_directory
        if sp_code_directory is None:
            raise RuntimeError('The sp_code_directory sphinx config value '
                               'must be set.')
        # localise the directory if given as an absolute path
        if sp_code_directory.startswith('/'):
            localised_directory = '.' + sp_code_directory
        else:
            localised_directory = sp_code_directory
        # check whether the directory exists
        if not os.path.exists(localised_directory):
            raise RuntimeError('The sp_code_directory ({}) does not '
                               'exist.'.format(localised_directory))

        # get the code file name for this particular swish box
        assert len(self.arguments) == 1, (
            'Just one argument -- code block id (possibly encoding the code '
            'file name -- expected')
        code_filename_id = self.arguments[0]
        assert code_filename_id.startswith('swish:'), (
            'The code box label ({}) must start with the "swish:" '
            'prefix.'.format(code_filename_id))
        assert not code_filename_id.endswith('.pl'), (
            'The code box label ({}) must not end with the ".pl" '
            'extension prefix.'.format(code_filename_id))
        # add the .pl extension as it is missing
        code_filename = '{}.pl'.format(code_filename_id[6:])

        # process the options -- they are used as HTML attributes
        attributes = {}

        # memorise implicit SWISH queries
        query_text = options.get('query-text', None)
        if query_text is not None:
            query_text = query_text.strip()
            attributes['query_text'] = query_text

        # memorise SWISH query box id
        query_id = options.get('query-id', None)
        if query_id is not None:
            id_collector = []
            for iid in query_id.strip().split(' '):
                iid = iid.strip()
                if not iid:
                    continue
                if not iid.startswith('swishq:'):
                    raise RuntimeError(
                        'The *query-id* parameter of a swish box '
                        'should start with the "swishq:" prefix.')
                if iid.endswith('.pl'):
                    raise RuntimeError(
                        'The *query-id* parameter of a swish box '
                        'should not use the ".pl" extension.')
                #####  existence of the query id is checked in the  #####
                #####  `check_inheritance_correctness` function     #####
                if iid in id_collector:
                    raise RuntimeError('The *{}* query block id provided via '
                                       'the *query-id* parameter of the *{}* '
                                       'code block is duplicated.'.format(
                                           iid, code_filename_id))
                else:
                    id_collector.append(iid)
            attributes['query_id'] = query_id

        # extract `inherit-id` (which may contain multiple ids) and memorise it
        inherit_id = options.get('inherit-id', None)
        inherit_id_collector = []
        if inherit_id is not None:
            for iid in inherit_id.strip().split(' '):
                iid = iid.strip()
                if not iid:
                    continue
                if not iid.startswith('swish:'):
                    raise RuntimeError('The *inherit-id* parameter of a swish '
                                       'box should start with the "swish:" '
                                       'prefix.')
                if iid.endswith('.pl'):
                    raise RuntimeError('The *inherit-id* parameter of a swish '
                                       'box should not use the ".pl" '
                                       'extension.')
                #####  existence of the inherited ids is checked in the  #####
                #####  `check_inheritance_correctness` function          #####
                if iid in inherit_id_collector:
                    raise RuntimeError('The *{}* code block id provided via '
                                       'the *inherit-id* parameter of the *{}* '
                                       'code block is duplicated.'.format(
                                           iid, code_filename_id))
                else:
                    inherit_id_collector.append(iid)
                # memorise that this code id will be inherited
                if not hasattr(env, 'sl_swish_inherited'):
                    env.sl_swish_inherited = dict()
                if iid in env.sl_swish_inherited:
                    env.sl_swish_inherited[iid].add(env.docname)
                else:
                    env.sl_swish_inherited[iid] = {env.docname}
            attributes['inherit_id'] = inherit_id

        # extract `source-text-start` and memorise it
        source_start = options.get('source-text-start', None)
        if source_start is not None:
            if not source_start.endswith('.pl'):
                source_start += '.pl'
            source_start_path = os.path.join(localised_directory, source_start)
            sphinx_prolog.file_exists(source_start_path)
            # memorise the association between the document and code box
            self.memorise_code(source_start, source_start_path)
            with open(source_start_path, 'r') as f:
                contents = f.read()
            # clean out the examples section
            raw_content = strip_examples_block(contents)
            attributes['source_text_start'] = '{}\n\n'.format(raw_content)
        # extract `source-text-end` and memorise it
        source_end = options.get('source-text-end', None)
        if source_end is not None:
            if not source_end.endswith('.pl'):
                source_end += '.pl'
            source_end_path = os.path.join(localised_directory, source_end)
            sphinx_prolog.file_exists(source_end_path)
            # memorise the association between the document and code box
            self.memorise_code(source_end, source_end_path)
            with open(source_end_path, 'r') as f:
                contents = f.read()
            # clean out the examples section
            raw_content = strip_examples_block(contents)
            attributes['source_text_end'] = '\n{}'.format(raw_content)

        # hide examples locally
        hide_examples = options.get('hide-examples', None)
        if hide_examples == '':
            hide_examples = True
        assert isinstance(hide_examples, bool) or hide_examples is None
        attributes['hide_examples'] = hide_examples

        # build a Prolog code file
        build_file = options.get('build-file', False)
        if build_file == '':
            build_file = True
        assert isinstance(build_file, bool)

        # if the content is given explicitly, use it instead of loading a file
        if self.content:
            contents = '\n'.join(self.content)

            # memorise the association between the document (a content source
            # file) and the code box
            self.memorise_code(code_filename_id, None, is_main_codeblock=True)
        else:
            # compose the full path to the code file and ensure it exists
            path_localised = os.path.join(localised_directory, code_filename)
            # path_original = os.path.join(sp_code_directory, code_filename)
            sphinx_prolog.file_exists(path_localised)

            # memorise the association between the document (a content source
            # file) and the code box -- this is used for watching for code file
            # updates
            self.memorise_code(code_filename_id, path_localised,
                               is_main_codeblock=True)

            # read in the code file and create a swish **code** node
            with open(path_localised, 'r') as f:
                contents = f.read()

        # compose a single Prolog file from inherit-id, source-text-start and
        # source-text-end parameters to be uploaded and sourced by SWISH
        if build_file:
            code_collector = []

            # load the inherited files
            if inherit_id_collector:
                assert 'inherit_id' in attributes
                for iid in inherit_id_collector:
                    iid_filename = '{}.pl'.format(iid[6:])
                    iid_path = os.path.join(localised_directory, iid_filename)
                    sphinx_prolog.file_exists(iid_path)
                    # memorise the association between the document and file
                    self.memorise_code(iid, iid_path)
                    with open(iid_path, 'r') as f:
                        iid_contents = f.read()
                    # clean out the examples section
                    iid_raw_content = strip_examples_block(iid_contents)
                    # add the inherited contents
                    code_collector.append(
                        '/*This part is inherited from: {}*/'.format(iid))
                    code_collector.append(iid_raw_content.strip())
                    code_collector.append(
                        '/*This is the end of inheritance.*/\n')
                del attributes['inherit_id']
            assert 'inherit_id' not in attributes

            # load the source-text-start contents
            if 'source_text_start' in attributes:
                code_collector.append('/*Begin ~source text start~*/')
                code_collector.append(attributes['source_text_start'].strip())
                code_collector.append('/*End ~source text start~*/\n')
                del attributes['source_text_start']
            assert 'source_text_start' not in attributes

            # load the code block contents
            code_collector.append(contents)

            # load the source-text-end contents
            if 'source_text_end' in attributes:
                code_collector.append('/*Begin ~source text end~*/')
                code_collector.append(attributes['source_text_end'].strip())
                code_collector.append('/*End ~source text end~*/\n')
                del attributes['source_text_end']
            assert 'source_text_end' not in attributes

            # get a name for this Prolog file
            build_file_name = '{}{}'.format(
                code_filename_id[6:], PROLOG_SUFFIX)

            # compose the file and save it in the temp directory
            temp_dir = os.path.join(env.app.confdir, PROLOG_TEMP_DIR)
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)
            temp_file = os.path.join(temp_dir, build_file_name)
            with open(temp_file, 'w') as f:
                f.write('\n'.join(code_collector))

            # get a request URL for this Prolog file
            sp_swish_book_url = env.config.sp_swish_book_url
            if sp_swish_book_url is None:
                raise RuntimeError('The sp_swish_book_url sphinx config value '
                                   'must be provided since the *{}* code '
                                   'block was set to use an external Prolog '
                                   'file via the *build-file* '
                                   'parameter.'.format(code_filename_id))
            prolog_temp_store = os.path.join(sp_swish_book_url, PROLOG_OUT_DIR)
            attributes['prolog_file'] = os.path.join(
                prolog_temp_store, build_file_name)

            # strip the content of the block from examples if requested
            hide_examples_global = env.config.sp_swish_hide_examples
            assert isinstance(hide_examples_global, bool)
            if hide_examples_global and hide_examples in (None, True):
                _hide_examples = True
            elif hide_examples_global and hide_examples is False:
                _hide_examples = False
            elif not hide_examples_global and hide_examples:
                _hide_examples = True
            elif not hide_examples_global and hide_examples in (None, False):
                _hide_examples = False
            else:
                assert False
            # hide each occurrence of the examples block
            if _hide_examples:
                contents = strip_examples_block(contents)
                # since we have already hidden examples here, we set the
                # hide_examples attribute to False to avoid repeating the step
                # in the visit_swish_code_node function
                attributes['hide_examples'] = False

        lang = 'Prolog'
        pre = swish_code(contents.strip(), contents,
                         ids=['{}-code'.format(
                             nodes.make_id(code_filename_id))],
                         label=code_filename_id,
                         language=lang,
                         **attributes)
        # create the outer swish node
        box = swish_box(language=lang)  # needed for syntax colouring
        # assign label and id (`ids=[nodes.make_id(code_filename_id)]`)
        self.options['name'] = code_filename_id
        self.add_name(box)

        # insert the swish code node into the outer node
        box += pre

        return [box]

    def memorise_code(self, code_filename_id, path_localised,
                      is_main_codeblock=False):
        """
        Memorises the association between the current document (a content
        source file containing the instantiation of the `swish` directive
        encoded by this object) and the code box.
        This procedure is also applied to *linked sources* (`source-text-start`
        and `source-text-end`) in addition to the code box itself.
        All of this information is stored in the `sl_swish_code` Sphinx
        environmental variable, which has the following structure::
            {'code_id': {'docs': set(docnames),
                         'main_doc': the_main_document_using_this_code_block,
                         'path': file_path_to_code_id,
                         'signature': creation_time_of_file_path_to_code_id},
             ...
            }
        Memorising this information allows to watch for changes in the code
        files and force Sphinx to rebuild pages that include swish boxes that
        depend upon them.

        `path` and `signature` are both `None` if the content of the SWISH box
        was given explicitly as the directive content.
        """
        env = self.state.document.settings.env

        if not hasattr(env, 'sl_swish_code'):
            env.sl_swish_code = {}

        # if code id has already been seen, verify that the code file has not
        # changed and add the document name to the watchlist for this code file
        if code_filename_id in env.sl_swish_code:
            # verify signature
            if path_localised is None:
                assert env.sl_swish_code[code_filename_id]['path'] is None
                assert env.sl_swish_code[code_filename_id]['signature'] is None
            else:
                if (os.path.getmtime(path_localised)
                        != env.sl_swish_code[code_filename_id]['signature']):
                    raise RuntimeError('A code file signature has changed '
                                       'during the runtime.')
            # add the document name to the set of dependent files
            env.sl_swish_code[code_filename_id]['docs'].add(env.docname)

            # check if this docname is the main one using this codeblock
            if is_main_codeblock:
                if env.sl_swish_code[code_filename_id]['main_doc'] is None:
                    env.sl_swish_code[code_filename_id]['main_doc'] = (
                        env.docname)
                else:
                    raise RuntimeError(
                        ('Only one code block can be created from each source '
                         'file. The code id {} is used by {} and cannot be '
                         'used by {}.').format(
                             code_filename_id,
                             env.sl_swish_code[code_filename_id]['main_doc'],
                             env.docname)
                    )
        # if code id has not been seen, create a new item storing its details
        else:
            if path_localised is None:
                timestamp = None
            else:
                timestamp = os.path.getmtime(path_localised)
            env.sl_swish_code[code_filename_id] = {
                'docs': {env.docname},
                'main_doc': env.docname if is_main_codeblock else None,
                'path': path_localised,
                'signature': timestamp
            }


def purge_swish_detect(app, env, docname):
    """
    Cleans the information stored in the Sphinx environment about documents
    with swish blocks (`sl_has_swish`), inherited ids (`sl_swish_inherited`)
    and the links between documents and swish code sources (`sl_swish_code`).
    If a document gets regenerated, the information whether this document
    has a swish directive is removed before the document is processed again.
    Similarly, links from code files to this document are purged.

    This function is hooked up to the `env-purge-doc` Sphinx event.
    """
    if hasattr(env, 'sl_has_swish'):
        # if the document was recorded to have a swish block and is now being
        # rebuilt, remove it from the store
        if docname in env.sl_has_swish:
            env.sl_has_swish.remove(docname)

    if hasattr(env, 'sl_swish_inherited'):
        nodes_to_remove = set()
        for inherit_id, docname_set in env.sl_swish_inherited.items():
            if docname in docname_set:
                docs_no = len(docname_set)
                if docs_no > 1:
                    docname_set.remove(docname)
                elif docs_no == 1:
                    docname_set.remove(docname)
                    nodes_to_remove.add(inherit_id)
                else:
                    assert inherit_id in nodes_to_remove
        for i in nodes_to_remove:
            del env.sl_swish_inherited[i]

    if hasattr(env, 'sl_swish_code'):
        nodes_to_remove = set()
        for code_id, code_node in env.sl_swish_code.items():
            # if the document was linked to any source code file and is now
            # being rebuilt, remove it from the appropriate stores
            if docname in code_node['docs']:
                docs_no = len(code_node['docs'])
                if docs_no > 1:
                    code_node['docs'].remove(docname)
                elif docs_no == 1:
                    code_node['docs'].remove(docname)
                    nodes_to_remove.add(code_id)
                else:
                    assert code_id in nodes_to_remove
            if docname == code_node['main_doc']:
                code_node['main_doc'] = None
        for i in nodes_to_remove:
            del env.sl_swish_code[i]


def merge_swish_detect(app, env, docnames, other):
    """
    In case documents are processed in parallel, the data stored in
    `sl_has_swish`, `sl_swish_inherited` and `sl_swish_code` Sphinx
    environment variables from different threads need to be merged.

    This function is hooked up to the `env-merge-info` Sphinx event.
    """
    if not hasattr(env, 'sl_has_swish'):
        env.sl_has_swish = set()
    if hasattr(other, 'sl_has_swish'):
        # join two sets by taking their union
        env.sl_has_swish |= other.sl_has_swish

    if not hasattr(env, 'sl_swish_inherited'):
        env.sl_swish_inherited = dict()
    if hasattr(other, 'sl_swish_inherited'):
        # join two sets by taking their union
        for key, val in other.sl_swish_inherited.items():
            if key in env.sl_swish_inherited:
                env.sl_swish_inherited[key] |= val
            else:
                env.sl_swish_inherited[key] = val

    if not hasattr(env, 'sl_swish_code'):
        env.sl_swish_code = {}
    if hasattr(other, 'sl_swish_code'):
        for key, val in other.sl_swish_code.items():
            # if this code file has already been referred to in another
            # document
            if key in env.sl_swish_code:
                # verify timestamp and path
                if ((env.sl_swish_code[key]['signature'] != val['signature'])
                        or (env.sl_swish_code[key]['path'] != val['path'])):
                    raise RuntimeError('A code file signature has changed '
                                       'during the runtime.')
                # join two sets by taking their union
                env.sl_swish_code[key]['docs'] |= val['docs']
                # choose the main document name
                if val['main_doc'] is not None:
                    if env.sl_swish_code[key]['main_doc'] is None:
                        env.sl_swish_code[key]['main_doc'] = val['main_doc']
                    else:
                        raise RuntimeError(
                            ('Two documents ({} and {}) are using the same '
                             'code file as a main source ().'
                             'file. The code id {} is used by {} and cannot be '
                             'used by {}.').format(
                                 val['main_doc'],
                                 env.sl_swish_code[key]['main_doc'],
                                 key)
                        )
            # if this code file has not yet been referred to
            else:
                # transfer the whole content
                env.sl_swish_code[key] = val


def inject_swish_detect(app, doctree, docname):
    """
    Injects call to the swish JavaScript library in documents that have swish
    code blocks.

    This function is hooked up to the `doctree-resolved` Sphinx event.
    """
    env = app.builder.env

    # if no swish code blocks were detected, skip this step
    if not hasattr(env, 'sl_has_swish'):
        return
    # if this document does not have any swish code blocks, skip this step
    if docname not in env.sl_has_swish:
        return

    # check for a user-specified SWISH server URL in the config
    sp_swish_url = env.config.sp_swish_url
    if sp_swish_url:
        call = 'swish:"{:s}"'.format(sp_swish_url)
    else:
        call = ''
    swish_function = ('\n\n    <script>$(function() {{ $(".swish").LPN('
                      '{{{}}}); }});</script>\n'.format(call))
    # `format='html'` is crucial to avoid escaping html characters
    script_node = nodes.raw(swish_function, swish_function, format='html')
    # add the call node to the document
    doctree.append(script_node)


def analyse_swish_code(app, env, added, changed, removed):
    """
    Ensures that when a code file is edited all the linked documents are
    updated.

    This function is hooked up to the `env-get-outdated` Sphinx event.
    """
    # skip this step if no swish code blocks were found
    if not hasattr(env, 'sl_swish_code'):
        return set()

    # check whether any code file has changed
    changed_code_files = set()
    for code_dict in env.sl_swish_code.values():
        # if the file still exists, check whether it has been updated
        if code_dict['path'] is not None:
            if os.path.exists(code_dict['path']):
                file_signature = os.path.getmtime(code_dict['path'])
                if file_signature != code_dict['signature']:
                    # check which files use this code file and refresh them
                    changed_code_files = changed_code_files.union(
                        code_dict['docs'])
            # if the file has been removed, refresh the affected docs
            else:
                changed_code_files = changed_code_files.union(
                    code_dict['docs'])
        else:
            assert code_dict['signature'] is None

    # disregard documents that are already marked to be updated or were
    # discarded
    changed_code_files -= removed | changed | added

    return changed_code_files


def check_inheritance_correctness(app, doctree, docname):
    """
    Checks whether SWISH ids provided via the `inherit-id` (code boxes) and
    `query-id` (query boxes) parameters exist.
    """
    # go through every swish code
    for node in doctree.traverse(swish_code):
        # get the inherit-id and query-id strings
        inherit_id = node.attributes.get('inherit_id', '')
        query_id = node.attributes.get('query_id', '')

        # we are only interested in the nodes that inherit something
        if inherit_id:
            # analyse each inherited id
            for iid_ in inherit_id.strip().split(' '):
                iid = iid_.strip()
                if not iid:
                    continue
                # check whether this id exists in the swish box record
                # the existence of the inherited file (if explicit content was
                # not given) should be checked upon its initialisation
                assert hasattr(app.env, 'sl_swish_code')
                if iid not in app.env.sl_swish_code:
                    raise RuntimeError('The inherited *{}* swish id does not '
                                       'exist.'.format(iid))

        # we are only interested in the nodes that reference a query
        if query_id:
            # check whether this id exists in the swish query record
            if not hasattr(app.env, 'sl_swish_query'):
                raise RuntimeError('A swish query box with *{}* id has not '
                                   'been found.'.format(query_id))
            # analyse each query id
            for iid_ in query_id.strip().split(' '):
                iid = iid_.strip()
                if not iid:
                    continue
                # check whether this id exists in the swish query record
                if iid not in app.env.sl_swish_query:
                    raise RuntimeError('The referenced swish query id *{}* does '
                                       'not exist.'.format(iid))


def assign_reference_title(app, document):
    """
    Update the labels record of the standard environment to allow referencing
    SWISH boxes.
    (See the `infobox.assign_reference_title` function for more details.)
    """
    # get the standard domain
    domain = app.env.get_domain('std')

    # go through every swish box
    for node in document.traverse(swish_box):
        # every swish box should have exactly one name starting with 'swish:'
        assert node['names']
        assert len(node['names']) == 1
        node_name = node['names'][0]
        if node_name.startswith('swish:'):
            refname = 'SWISH code box'
        elif node_name.startswith('swishq:'):
            refname = 'SWISH query box'
        else:
            assert 0, 'SWISH box ids must either start with swish: or swishq:'

        # every swish box has a single id
        assert len(node['ids']) == 1
        node_id = node['ids'][0]

        # get the document name
        docname = app.env.docname

        # every swish box should **already** be referenceable without a title
        assert node_name in domain.anonlabels
        assert domain.anonlabels[node_name] == (docname, node_id)

        # allow this swish box to be referenced with the default
        # 'SWISH code box' or 'SWISH query box' stub
        domain.labels[node_name] = (docname, node_id, refname)


#### SWISH query directive ####################################################


class swish_query(nodes.literal, nodes.Element):  # nodes.literal_block
    """A `docutils` node holding Simply Logical swish queries."""


def visit_swish_query_node(self, node):
    """
    Builds an opening HTML tag for Simply Logical swish queries.

    For inline queries this method only builds the opening tag.
    For display queries, on the other hand, it appends the opening tag,
    the (syntax highlighted) content and the closing tag.
    Since the latter operation requires the content to be formatted before
    appending it to the document body, the automatic contend embedding is
    disabled.
    This is achieved by raising the `nodes.SkipNode` exception, the artifact
    of which is not executing the `depart_swish_query_node` method, hence this
    method must also append the closing tag for display queries.

    Inspiration for the code syntax highlighting was taken from
    https://github.com/sphinx-doc/sphinx/blob/7ecf6b88aa5ddaed552527d2ef60f1bd35e98ddc/sphinx/writers/html5.py#L384
    """
    env = self.document.settings.env

    # get node id
    node_ids = node.get('ids', [])
    assert len(node_ids) == 1
    assert node_ids[0].startswith('swishq')
    assert node_ids[0].endswith('-query')
    #
    node_label = node.get('label', None)
    assert node_label is not None
    assert node_ids[0] == '{}-query'.format(nodes.make_id(node_label))

    attributes = dict()
    # composes the `source-id` HTML attribute if present
    source_id = node.attributes.get('source_id', None)
    if source_id is not None:
        if not hasattr(env, 'sl_swish_code'):
            raise RuntimeError('A swish code box with *{}* id has not '
                               'been found.'.format(source_id))
        iid = []
        for i_ in source_id.strip().split(' '):
            i = i_.strip()
            if not i:
                continue
            iid.append('{}-code'.format(nodes.make_id(i)))
            # ensure that all of the source code blocks are also in this
            # document as otherwise the query export JavaScript will not work
            if env.sl_swish_code[i]['main_doc'] not in self.docnames:
                raise RuntimeError(
                    ('The query block *{}* placed in *{}* document exports to '
                     '*{}*, which is in a different document (*{}*). '
                     'Query export via the *source-id* parameter only works '
                     'in a scope of a single document.'.format(
                         node_label, self.docnames, i,
                         env.sl_swish_code[i]['main_doc']))
                )
        attributes['source-id'] = ' '.join(iid)

    inline = node.attributes.get('inline', None)
    assert inline is not None and isinstance(inline, bool)
    lang = node.attributes.get('language')
    if inline:
        assert lang is None
        starttag = self.starttag(
            node, 'code', CLASS=('swish query'), **attributes)
        self.body.append(starttag)
    else:
        # ensure Prolog syntax highlighting
        assert lang == 'Prolog', 'SWISH query blocks must be Prolog syntax'
        starttag = self.starttag(  # pre -> div # literal / literal-block
            node, 'div', suffix='',
            CLASS='swish query highlight-{} notranslate'.format(lang))
        highlighted = self.highlighter.highlight_block(
            node.rawsource, lang, location=node)
        self.body.append(starttag + highlighted)
        # lack of `\n` after the `code` tag ensures correct spacing of the text
        # (see the depart_swish_query_node method for more details)
        self.body.append('</div>\n')
        # otherwise the raw content is inserted and
        # the `depart_swish_query_node` method is executed
        raise nodes.SkipNode


def depart_swish_query_node(self, node):
    """Builds a closing HTML tag for Simply Logical swish queries."""
    inline = node.attributes.get('inline', None)
    assert inline is not None and isinstance(inline, bool)
    # lack of `\n` after the `code` tag ensures correct spacing of the text
    inline_tag = '</code>' if inline else '</div>\n'  # pre -> div

    self.body.append(inline_tag)


def visit_swish_query_node_(self, node):
    """
    Builds a prefix for embedding Simply Logical swish queries in LaTeX and raw
    text.
    """
    raise NotImplemented


def depart_swish_query_node_(self, node):
    """
    Builds a postfix for embedding Simply Logical swish queries in LaTeX and
    raw text.
    """
    raise NotImplemented


def swish_q(name, rawtext, text, lineno, inliner, options={}, content=[]):
    """
    Defines the `swish-query` role for building **inline** Simply Logical swish
    query boxes.
    The `swish-query` role is of the form::
       :swish-query:`?-my_query(a,X). <swishq:1.2.3>`

    All of the ids need to be **prefixed** with `swishq:`.
    The ids are defined within angle brackets at the very end of the role
    text.
    This role operates on one Sphinx environmental variable:

    sl_swish_query
      A dictionary encoding the association between query ids and documents in
      which these queries are embedded (one document per **unique** id).

    See the `SWISHq` class (`swish-query` directive) for more details.
    This implementation was inspired by:
    https://doughellmann.com/blog/2010/05/09/defining-custom-roles-in-sphinx/

    ---

    Parameters:

    * `name` -- the role name used in the document;
    * `rawtext` -- the entire markup snippet including the role name;
    * `text` -- the content of the role;
    * `lineno` -- the line number where rawtext appears in the input document;
    * `inliner` -- the inliner instance that called this function;
    * `options` -- role options for customisation (supplied via the `role`
      directive); and
    * `content` -- the directive content for customisation.

    Return values:

    1. a list of nodes to insert into the document (can be empty); and
    2. a list of system messages used for displaying errors (can be empty).
    """
    assert name == 'swish-query'
    env = inliner.document.settings.env

    # get the query box id
    matches = LABEL_PATTERN.findall(text)
    if len(matches) != 1:
        raise RuntimeError('Expected exactly one label in *{}*, but {} were '
                           'found: {}.'.format(text, len(matches), matches))
    block_id = matches[0]
    text = re.sub('\s*<{}>'.format(block_id),
                  '',
                  text,
                  flags=(re.M | re.I | re.S))
    assert block_id not in text
    assert block_id.startswith('swishq:'), (
        'The query block label ({}) must start with the "swishq:" '
        'prefix.'.format(block_id))
    assert not block_id.endswith('.pl'), (
        'The query block label ({}) must not end with the ".pl" '
        'extension prefix.'.format(block_id))

    # memorise the association between query id and document name and
    # check for duplicate names
    if not hasattr(env, 'sl_swish_query'):
        env.sl_swish_query = dict()
    if block_id in env.sl_swish_query:
        raise RuntimeError(
            'The {} swish query label is duplicated.'.format(block_id))
    else:
        env.sl_swish_query[block_id] = env.docname

    # force inline
    inline = True

    # content is required
    text_ = text.strip()
    if not text_:
        raise RuntimeError(
            'The {} swish query box must have content.'.format(block_id))

    # build the query node
    pre = swish_query(text_, text,
                      ids=['{}-query'.format(nodes.make_id(block_id))],
                      label=block_id,
                      inline=inline)

    # create the outer swish node
    box = swish_box(inline=inline)
    # assign label and id (`ids=[nodes.make_id(block_id)]`)
    # https://sourceforge.net/p/docutils/code/HEAD/tree/trunk/docutils/docutils/parsers/rst/__init__.py#l392
    name = nodes.fully_normalize_name(block_id)
    if 'name' in box:
        del box['name']
    box['names'].append(name)
    inliner.document.note_explicit_target(box, box)

    # insert the swish code node into the outer node
    box += pre

    return [box], []


class SWISHq(Directive):
    """
    Defines the `swish-query` directive for building **display** Simply Logical
    swish query boxes.
    The `swish-query` directive is of the form::
       .. swish-query:: swishq:1.2.3 (required)
          :source-id: swish:1.0.0 [swish:1.0.1 swish:1.0.2] (optional)

          ?-my_query(a,X).

    All of the ids need to be **prefixed** with `swishq:`.
    This directive operates on one Sphinx environmental variable:

    sl_swish_query
      A dictionary encoding the association between query ids and documents in
      which these queries are embedded (one document per **unique** id).
    """
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = False
    has_content = True
    option_spec = {'source-id': directives.unchanged}

    def run(self):
        """Builds a swish query box."""
        env = self.state.document.settings.env
        options = self.options

        # get the query box id
        assert len(self.arguments) == 1, (
            'Just one argument -- query box id -- expected')
        block_id = self.arguments[0].strip()
        assert block_id.startswith('swishq:'), (
            'The query block label ({}) must start with the "swishq:" '
            'prefix.'.format(block_id))
        assert not block_id.endswith('.pl'), (
            'The query block label ({}) must not end with the ".pl" '
            'extension prefix.'.format(block_id))

        # memorise the association between query id and document name and
        # check for duplicate names
        if not hasattr(env, 'sl_swish_query'):
            env.sl_swish_query = dict()
        if block_id in env.sl_swish_query:
            raise RuntimeError(
                'The {} swish query label is duplicated.'.format(block_id))
        else:
            env.sl_swish_query[block_id] = env.docname

        attributes = dict()
        # memorise SWISH query box id
        source_id = options.get('source-id', None)
        if source_id is not None:
            id_collector = []
            for iid in source_id.strip().split(' '):
                iid = iid.strip()
                if not iid:
                    continue
                if not iid.startswith('swish:'):
                    raise RuntimeError(
                        'The *source-id* parameter of a swish query box '
                        'should start with the "swish:" prefix.')
                if iid.endswith('.pl'):
                    raise RuntimeError(
                        'The *source-id* parameter of a swish query box '
                        'should not use the ".pl" extension.')
                #####  existence of the query id is checked in the  #####
                #####  `check_sourceid_correctness` function        #####
                if iid in id_collector:
                    raise RuntimeError('The *{}* code block id provided via '
                                       'the *source-id* parameter of the *{}* '
                                       'query block is duplicated.'.format(
                                           iid, block_id))
                else:
                    id_collector.append(iid)
            attributes['source_id'] = source_id

        # force display
        inline = False

        # content is required
        if not self.content:
            raise RuntimeError(
                'The {} swish query box must have content.'.format(block_id))

        # build the query node
        contents = '\n'.join(self.content)
        pre = swish_query(contents.strip(), contents,
                          ids=['{}-query'.format(nodes.make_id(block_id))],
                          inline=inline,
                          label=block_id,
                          language='Prolog',
                          **attributes)

        # create the outer swish node
        box = swish_box(inline=inline)
        # assign label and id (`ids=[nodes.make_id(block_id)]`)
        self.options['name'] = block_id
        self.add_name(box)

        # insert the swish code node into the outer node
        box += pre

        return [box]


def purge_swish_query(app, env, docname):
    """
    Cleans the information stored in the Sphinx environment about documents
    with swish query blocks (`sl_swish_query`).
    If a document gets regenerated, the information about the queries embedded
    within this document is removed before the document is processed again.

    This function is hooked up to the `env-purge-doc` Sphinx event.
    """
    if hasattr(env, 'sl_swish_query'):
        # if the document was recorded to have a swish query block and is now
        # being rebuilt, remove it from the store
        purge = []
        for key, value in env.sl_swish_query.items():
            if value == docname:
                purge.append(key)
        for key in purge:
            del env.sl_swish_query[key]
            assert key not in env.sl_swish_query


def merge_swish_query(app, env, docnames, other):
    """
    In case documents are processed in parallel, the data stored in the
    `sl_swish_query` Sphinx environment variable from different threads need
    to be merged.

    This function is hooked up to the `env-merge-info` Sphinx event.
    """
    if not hasattr(env, 'sl_swish_query'):
        env.sl_swish_query = dict()
    if hasattr(other, 'sl_swish_query'):
        for key in other.sl_swish_query:
            # check for duplicates
            if key in env.sl_swish_query:
                raise RuntimeError('Multiple documents have a swish query '
                                   'with the same id.'.format(key))
            else:
                env.sl_swish_query[key] = other.sl_swish_query[key]


def check_sourceid_correctness(app, doctree, docname):
    """
    Checks whether SWISH ids provided via the `source-id` (query boxes)
    parameter exist.
    """
    # go through every swish query box
    for node in doctree.traverse(swish_query):
        # get the source-id string
        source_id = node.attributes.get('source_id', '').strip()

        # we are only interested in the nodes that export something
        if source_id:
            # check whether this id exists in the swish query record
            if not hasattr(app.env, 'sl_swish_code'):
                raise RuntimeError('A swish code box with *{}* id has not '
                                   'been found.'.format(source_id))
            # analyse each query id
            for iid_ in source_id.strip().split(' '):
                iid = iid_.strip()
                if not iid:
                    continue
                # check whether this id exists in the swish code record
                if iid not in app.env.sl_swish_code:
                    raise RuntimeError('The referenced swish code id *{}* '
                                       'does not exist.'.format(iid))


def move_prolog_files(app, exc):
    """
    Copies Prolog files composed via the `build-file` parameter to the build
    directory.
    (Attached to the `build-finished` Sphinx event.)
    """
    # check build success
    if exc is not None:  # the build failed
        return
    # get Prolog file request URL
    sp_swish_book_url = app.env.config.sp_swish_book_url
    if sp_swish_book_url is None:  # a request URL is not given
        return
    # check existence of the temp storage (source) director
    temp_dir = os.path.join(app.confdir, PROLOG_TEMP_DIR)
    if not os.path.exists(temp_dir):  # the temp directory is missing
        return

    # compose the build directory path and ensure its existence
    out_dir = os.path.join(app.outdir, PROLOG_OUT_DIR)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    # copy all the Prolog files
    for path in glob.glob(os.path.join(temp_dir, '*{}'.format(PROLOG_SUFFIX))):
        assert path.endswith(PROLOG_SUFFIX)
        fname = os.path.basename(path)
        assert fname.endswith(PROLOG_SUFFIX)
        # copyfile only copies if the file does not exist or differs
        sphinx.util.osutil.copyfile(path, os.path.join(out_dir, fname))


#### Extension setup ##########################################################


def include_static_files(app):
    """
    Copies the static files required by this extension.
    (Attached to the `builder-inited` Sphinx event.)
    """
    for file_name in STATIC_FILES:
        file_path = sphinx_prolog.get_static_path(file_name)
        if file_path not in app.config.html_static_path:
            app.config.html_static_path.append(file_path)


def setup(app):
    """
    Sets up the Sphinx extension for the `swish` directive.
    """
    # register the two Sphinx config values used for the extension
    app.add_config_value('sp_code_directory', None, 'env')
    app.add_config_value('sp_swish_url', '', 'env')
    app.add_config_value('sp_swish_book_url', None, 'env')
    app.add_config_value('sp_swish_hide_examples', False, 'env')

    # register the custom docutils nodes with Sphinx
    app.add_node(
        swish_box,
        html=(visit_swish_box_node, depart_swish_box_node),
        latex=(visit_swish_box_node_, depart_swish_box_node_),
        text=(visit_swish_box_node_, depart_swish_box_node_)
    )
    app.add_node(
        swish_code,
        html=(visit_swish_code_node, depart_swish_code_node),
        latex=(visit_swish_code_node_, depart_swish_code_node_),
        text=(visit_swish_code_node_, depart_swish_code_node_)
    )
    app.add_node(
        swish_query,
        html=(visit_swish_query_node, depart_swish_query_node),
        latex=(visit_swish_query_node_, depart_swish_query_node_),
        text=(visit_swish_query_node_, depart_swish_query_node_)
    )

    # ensure the required auxiliary files are included in the Sphinx build
    app.connect('builder-inited', include_static_files)
    for css_file in STATIC_CSS_FILES:
        if not sphinx_prolog.is_css_registered(app, css_file):
            app.add_css_file(css_file)
    for js_file in STATIC_JS_FILES:
        if not sphinx_prolog.is_js_registered(app, js_file):
            app.add_js_file(js_file)

    # register the custom role and directives with Sphinx
    app.add_role('swish-query', swish_q)
    app.add_directive('swish', SWISH)
    app.add_directive('swish-query', SWISHq)

    # connect custom hooks to the Sphinx build process
    app.connect('env-purge-doc', purge_swish_detect)
    app.connect('env-merge-info', merge_swish_detect)
    app.connect('doctree-read', assign_reference_title)
    app.connect('doctree-resolved', check_inheritance_correctness)
    app.connect('doctree-resolved', inject_swish_detect)
    app.connect('env-get-outdated', analyse_swish_code)
    app.connect('env-purge-doc', purge_swish_query)
    app.connect('env-merge-info', merge_swish_query)
    app.connect('doctree-resolved', check_sourceid_correctness)
    app.connect('build-finished', move_prolog_files)

    return {'version': sphinx_prolog.VERSION}
