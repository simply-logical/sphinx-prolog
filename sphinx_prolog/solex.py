# Copyright (C) 2020
# Author: Kacper Sokol <k.sokol@bristol.ac.uk>
# License: new BSD
"""
Implements the `exercise` and `solution` directives for Jupyter Book and
Sphinx.
"""

import os

from docutils import nodes
from docutils.parsers.rst import Directive

import sphinx_prolog

STATIC_FILE = 'sphinx-prolog.css'

#### Exercise directive #######################################################


class exercise(nodes.Admonition, nodes.Element):
    """A `docutils` node holding Simply Logical exercises."""


def visit_exercise_node(self, node):
    """
    Builds an opening HTML tag for Simply Logical exercises.

    Overrides `Sphinx's HTML5 generator <https://github.com/sphinx-doc/sphinx/blob/3.x/sphinx/writers/html5.py#L53>`_.
    """
    self.body.append(self.starttag(
        node, 'div', CLASS=('admonition exercise')))


def depart_exercise_node(self, node):
    """
    Builds a closing HTML tag for Simply Logical exercises.

    Overrides `Sphinx's HTML5 generator <https://github.com/sphinx-doc/sphinx/blob/3.x/sphinx/writers/html5.py#L53>`_.
    """
    self.body.append('</div>\n')


def visit_exercise_node_(self, node):
    """
    Builds a prefix for embedding Simply Logical exercises in LaTeX and raw
    text.
    """
    raise NotImplemented
    self.visit_admonition(node)


def depart_exercise_node_(self, node):
    """
    Builds a postfix for embedding Simply Logical exercises in LaTeX and raw
    text.
    """
    raise NotImplemented
    self.depart_admonition(node)


class exercise_title(nodes.title):
    """A `docutils` node holding the **title** of Simply Logical exercises."""


def visit_exercise_title_node(self, node):
    """
    Builds an opening HTML tag for the **title** node of the Simply Logical
    exercises.

    Overrides Sphinx's HTML5
    `visit title <https://github.com/sphinx-doc/sphinx/blob/68cc0f7e94f360a2c62ebcb761f8096e04ebf07f/sphinx/writers/html5.py#L355>`_.

    Note: `self` is of a `writer` type.
    """
    assert self.builder.name != 'singlehtml', (
        'This function is not suitable for singlehtml builds -- '
        'see the URL in the docstring.')
    if not isinstance(node, exercise_title):
        raise RuntimeError('This function should only be used to process '
                           'an exercise title.')
    if not isinstance(node.parent, exercise):
        raise RuntimeError('This function should only be used to process '
                           'an exercise title that is embedded within an '
                           'exercise node.')
    assert len(node.parent['ids']) == 1, (
        'Exercise nodes need to be ided to be referenceable.')

    # self.body.append(self.starttag(node, 'p', CLASS=('admonition-title')))
    # alternative_visit_title(self, node)
    #
    self.visit_title(node)


def source_exercise_target(self, node):
    """Collects `docname`, `id` and `fignumber` of a linked exercise."""
    std_domain = self.builder.env.domains['std']
    figtype = std_domain.get_enumerable_node_type(node.parent)
    assert figtype == 'solution'

    fig_id = node.parent['ids'][0]

    # sort out the label
    exercise_label = node.parent.attributes['exercise']

    names = node.parent['names']
    assert len(names) == 1
    assert names[0].startswith('sol:')

    # get exercise id
    assert fig_id.startswith('sol-')
    exercise_id = 'ex-{}'.format(fig_id[4:])
    assert exercise_id == nodes.make_id(exercise_label)

    # because the exercise may be in a different document, we go global
    all_labels = std_domain.data['labels']
    assert exercise_label in all_labels

    # track down the document and identifier
    exercise_source_docname = all_labels[exercise_label][0]
    fig_identifiers = self.builder.env.toc_fignumbers
    assert exercise_source_docname in fig_identifiers
    assert 'exercise' in fig_identifiers[exercise_source_docname]
    ex_docname_map = fig_identifiers[exercise_source_docname]['exercise']
    assert exercise_id in ex_docname_map

    fignumber = ex_docname_map[exercise_id]

    return exercise_source_docname, exercise_id, fignumber


def source_solution_target(self, node):
    """
    Collects `docname`, `id` and `fignumber` of a linked solution if it exists.
    """
    std_domain = self.builder.env.domains['std']
    figtype = std_domain.get_enumerable_node_type(node.parent)
    assert figtype == 'exercise'

    # sort out the label
    names = node.parent['names']
    assert len(names) == 1
    exercise_label = names[0]
    assert exercise_label.startswith('ex:')

    # get solution id
    solution_label = 'sol:{}'.format(exercise_label[3:])
    solution_id = nodes.make_id(solution_label)

    # because the solution may be in a different document, we go global
    all_labels = std_domain.data['labels']
    if solution_label not in all_labels:
        return None

    # track down the document and identifier
    solution_source_docname = all_labels[solution_label][0]
    fig_identifiers = self.builder.env.toc_fignumbers
    assert solution_source_docname in fig_identifiers
    assert 'solution' in fig_identifiers[solution_source_docname]
    sol_docname_map = fig_identifiers[solution_source_docname]['solution']
    assert solution_id in sol_docname_map

    fignumber = sol_docname_map[solution_id]

    return solution_source_docname, solution_id, fignumber


def alternative_visit_title(self, node):
    """
    Provides an alternative implementation of Sphinx's HTML5 `add_fignumber`.

    See `here <https://github.com/sphinx-doc/sphinx/blob/68cc0f7e94f360a2c62ebcb761f8096e04ebf07f/sphinx/writers/html5.py#L280>`_ for more details.
    """
    std_domain = self.builder.env.domains['std']

    # get the figtype from the parent of this node since titles are not
    # enumerable
    figtype = std_domain.get_enumerable_node_type(node.parent)

    if figtype is None:
        raise RuntimeError('The figtype was not found despite the '
                           'exercise_title node being used within an exercise '
                           'node.')

    assert figtype in ('exercise', 'solution')

    # get the map of figure numbers for exercises for this document
    # if figtype is solution, we need to get a number of the corresponding
    # exercise
    fig_map = self.builder.fignumbers.get(figtype, {})

    # get id the exercise node
    fig_id = node.parent['ids'][0]
    # get figure number of the exercise node
    assert fig_id in fig_map

    if figtype == 'solution':
        _, _, fig_number = source_exercise_target(self, node)
    else:
        fig_number = fig_map[fig_id]

    # stringify the exercise id
    fig_number_str = '.'.join(map(str, fig_number))

    # format the exercise id
    prefix = self.builder.config.numfig_format.get(figtype)
    assert prefix is not None, 'exercise fignum format is not defined.'
    exercise_title = prefix % fig_number_str

    # build the HTML structure
    self.body.append('<span class="caption-number">')
    self.body.append(exercise_title + ' ')
    self.body.append('</span>')


def depart_exercise_title_node(self, node):
    """
    Builds a closing HTML tag for the **title** node of the Simply Logical
    exercises.

    Overrides `Sphinx's HTML5 generator <https://github.com/sphinx-doc/sphinx/blob/68cc0f7e94f360a2c62ebcb761f8096e04ebf07f/sphinx/writers/html5.py#L362>`_.
    """
    if (self.permalink_text and self.builder.add_permalinks
            and node.parent.hasattr('ids') and node.parent['ids']):
        self.add_permalink_ref(node.parent, 'Permalink to this exercise')
    else:
        raise RuntimeError('Could not add a permalink to an exercise box.')

    # get a URL to the exercise
    sol = source_solution_target(self, node)
    if sol is not None:
        docname, id_, _ = sol
        url = self.builder.get_relative_uri(
            self.builder.current_docname, docname)
        # self.builder.env.doc2path(docname, base=None)
        content = ('<a href="{}#{}" class="solution-link" '
                   'title="Go to the solution"></a>')
        self.body.append(content.format(url, id_))

    # finish the title
    # self.body.append('</span>\n')
    #
    self.depart_title(node)


def visit_exercise_title_node_(self, node):
    """
    Builds a prefix for embedding the **title** of Simply Logical exercises in
    LaTeX and raw text.
    """
    raise NotImplemented


def depart_exercise_title_node_(self, node):
    """
    Builds a postfix for embedding the **title** of Simply Logical exercises in
    LaTeX and raw text.
    """
    raise NotImplemented


class Exercise(Directive):
    """
    Defines and processes the `exercise` directive, which is of the form::
       .. exercise:: ex:2.9

         Exercise content. (optional)

    `ex:2.9` is a label that can be referred to either with ``:ref:`ex:2.9```
    to get a hyperlink saying *exercise* (see the `exercise_title_getter`
    function), or with `` :numref:`ex:2.9` `` to get a numbered reference based
    on the `numfig_format` for `exercise` (see the `set_exercise_numfig_format`
    function), which by default is defined as `Exercise %s`. To change this
    stub the `numfig_format.exercise` Sphinx setting variable can be set to the
    desired string formatter.

    If the `exercise` directive has content, it will be used to fill in the
    exercise box. Otherwise, a file name with striped `ex:` and appended `.md`
    will be located in the exercise directory provided by the user through the
    `sp_exercise_directory` Sphinx configuration parameter.

    Notes:
        `env.domaindata['std']` and `env.domains['std']` hold the reference
        catalogue.

        Giving an exercise node an id (via
        `exercise(content, ids=[unique_id])`) ensures that it gets a `numfig`
        assigned. When assigning a name via `self.add_name(node)`, this is done
        automatically. To get a nice id string we can use the
        `nodes.make_id(name)` function.

        Other useful arguments for creating a node are:

        * `ids=[id_]`,
        * `names=[label]`,
        * `label=label`,
        * `title=label`,
        * `docname=env.docname`.

        The inspiration for this directive -- in particular to make it
        referenceable and enumerable -- was taken from:

        * https://github.com/sphinx-doc/sphinx/blob/68cc0f7e94f360a2c62ebcb761f8096e04ebf07f/sphinx/directives/patches.py#L166
        * https://github.com/sphinx-doc/sphinx/blob/68cc0f7e94f360a2c62ebcb761f8096e04ebf07f/sphinx/directives/patches.py#L42

        and

        * https://docutils.sourceforge.io/docs/ref/doctree.html#names
        * https://docutils.sourceforge.io/docs/ref/rst/directives.html#common-options

        The latter two documents show the importance, universality and
        portability of the `name` option for a directive, and the former two
        show how to assign it on the fly if a directive was not given a `name`
        in the first place.
    """
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = False
    has_content = True
    option_spec = {}

    def run(self):
        """Builds an exercise box with a title."""
        # NOTE: since this directive has a complementary `solution` directive
        #       it may be better to put the two in a separate `exercise` domain
        env = self.state.document.settings.env

        # get the user-provided label of the exercise
        label = self.arguments[0]
        assert label.startswith('ex:'), (
            'The exercise label ({}) must start with the "ex:" prefix.'.format(
                label))

        if self.content:
            content_string = '\n'.join(self.content)
            content_list = self.content
            content_offset = self.content_offset
        else:
            content_string = read_exercise(env, label)
            content_list = content_string.split('\n')
            content_offset = 0

        # we do not assign an id to this node (despite it being a prerequisite
        # for assigning it a fignum) as this will happen automatically when
        # a name is assigned to this node
        exercise_content_node = exercise(content_string)

        # since the label of the node was not given in the standard docutil
        # manner (via the optional `name` parameter), it needs to be manually
        # assigned to this instance of the exercise directive and processed,
        # i.e., it registers the label with the domain (standard `std` domain
        # in this case); it also checks whether the labels is not duplicated
        self.options['name'] = label
        self.add_name(exercise_content_node)
        # these steps ensure that the node created by this directive can be
        # referenced with `ref` and `numref`

        # build an empty exercise title, the fignum is injected when building
        # its HTML representation
        exercise_title_node = exercise_title()

        # add title to the exercise and process the content
        exercise_content_node += exercise_title_node
        self.state.nested_parse(
            content_list, content_offset, exercise_content_node)

        return [exercise_content_node]


def exercise_title_getter(node):
    """
    Defines the default calling name (accessed via :ref:`ex:1.1`) of an
    exercise node.
    """
    assert isinstance(node, exercise)
    return 'exercise'


def set_exercise_numfig_format(app, config):
    """
    Initialises the default `fignum_format` for the enumerated `exercise` node.

    This is needed as setting the default `numfig` format as follows::
        app.config.numfig_format.setdefault('exercise', 'Exercise %s')
    in the `setup(app)` function as shown `here
    <https://github.com/sphinx-doc/sphinx/blob/af62fa61e6cbd88d0798963211e73e5ba0d55e6d/tests/roots/test-add_enumerable_node/enumerable_node.py#L62>`_
    does not work.

    This function is hooked up to the `config-inited` Sphinx event.
    """
    numfig_format = {'exercise': 'Exercise %s'}

    # override the default numfig format with values in the config file
    numfig_format.update(config.numfig_format)
    config.numfig_format = numfig_format


def read_exercise(env, label):
    """
    Reads in a file containing the exercise linked to the `label`.
    """
    # checks whether the exercise location is set by the user
    sl_ex_directory = env.config.sp_exercise_directory
    if sl_ex_directory is None:
        raise RuntimeError('The sp_exercise_directory sphinx config '
                           'value must be set.')
    # localise the directory if given as an absolute path
    if sl_ex_directory.startswith('/'):
        localised_directory = '.' + sl_ex_directory
    else:
        localised_directory = sl_ex_directory
    # check whether the directory exists
    if not os.path.exists(localised_directory):
        raise RuntimeError('The sp_exercise_directory ({}) does not '
                           'exist.'.format(localised_directory))

    # format the filename
    assert not label.endswith('.md')
    if label.startswith('ex:'):
        exercise_id = label[3:]
    elif label.startswith('sol:'):
        exercise_id = label[4:]
    else:
        raise RuntimeError('The label either has to start with "ex:" or '
                           '"sol:".')

    filename = '{}.md'.format(exercise_id)
    exercise_path = os.path.join(localised_directory, filename)

    # ensure that the file exists
    sphinx_prolog.file_exists(exercise_path)

    # read the file
    with open(exercise_path, 'r') as f:
        exercise_content = f.read()

    # add this file to watch list for rebuilding this document
    env.note_dependency(exercise_path)

    return exercise_content


#### Solution directive #######################################################


class solution(nodes.Admonition, nodes.Element):
    """A `docutils` node holding Simply Logical solution."""


def visit_solution_node(self, node):
    """See the coresponding exercise function."""
    self.body.append(self.starttag(
        node, 'div', CLASS=('admonition solution')))


def depart_solution_node(self, node):
    """See the coresponding exercise function."""
    self.body.append('</div>\n')


def visit_solution_node_(self, node):
    """See the coresponding exercise function."""
    raise NotImplemented
    self.visit_admonition(node)


def depart_solution_node_(self, node):
    """See the coresponding exercise function."""
    raise NotImplemented
    self.depart_admonition(node)


class solution_title(nodes.title):
    """A `docutils` node holding the **title** of Simply Logical solution."""


def visit_solution_title_node(self, node):
    """See the coresponding exercise function."""
    assert self.builder.name != 'singlehtml', (
        'This function is not suitable for singlehtml builds -- '
        'see the URL in the docstring.')
    if not isinstance(node, solution_title):
        raise RuntimeError('This function should only be used to process '
                           'a solution title.')
    if not isinstance(node.parent, solution):
        raise RuntimeError('This function should only be used to process '
                           'a solution title that is embedded within an '
                           'solution node.')
    assert len(node.parent['ids']) == 1, (
        'Solution nodes need to be ided to be referenceable.')

    self.body.append(self.starttag(node, 'p', CLASS=('admonition-title')))
    alternative_visit_title(self, node)


def depart_solution_title_node(self, node):
    """See the coresponding exercise function."""
    if (self.permalink_text and self.builder.add_permalinks
            and node.parent.hasattr('ids') and node.parent['ids']):
        self.add_permalink_ref(node.parent, 'Permalink to this solution')
    else:
        raise RuntimeError('Could not add a permalink to an solution box.')

    # get a URL to the exercise
    docname, id_, _ = source_exercise_target(self, node)
    url = self.builder.get_relative_uri(self.builder.current_docname, docname)
    # self.builder.env.doc2path(docname, base=None)
    content = ('<a href="{}#{}" class="exercise-link" '
               'title="Go to the exercise"></a>')
    self.body.append(content.format(url, id_))

    # finish the title
    self.body.append('</p>\n')


def visit_solution_title_node_(self, node):
    """See the coresponding exercise function."""
    raise NotImplemented


def depart_solution_title_node_(self, node):
    """See the coresponding exercise function."""
    raise NotImplemented


class Solution(Directive):
    """See the coresponding exercise function."""
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = False
    has_content = True
    option_spec = {}

    def run(self):
        """See the coresponding exercise function."""
        env = self.state.document.settings.env

        label = self.arguments[0]
        assert label.startswith('ex:'), (
            'The solution label ({}) must start with the "ex:" prefix and '
            'link to an existing exercise.'.format(label))
        sol_label = 'sol:{}'.format(label[3:])

        if self.content:
            content_string = '\n'.join(self.content)
            content_list = self.content
            content_offset = self.content_offset
        else:
            content_string = read_exercise(env, label)
            content_list = content_string.split('\n')
            content_offset = 0

        solution_content_node = solution(content_string, exercise=label)

        self.options['name'] = sol_label
        self.add_name(solution_content_node)

        solution_title_node = solution_title()

        solution_content_node += solution_title_node
        self.state.nested_parse(
            content_list, content_offset, solution_content_node)

        return [solution_content_node]


def solution_title_getter(node):
    """See the coresponding exercise function."""
    assert isinstance(node, solution)
    return 'solution'


def set_solution_numfig_format(app, config):
    """See the coresponding exercise function."""
    numfig_format = {'solution': 'Solution %s'}

    # override the default numfig format with values in the config file
    numfig_format.update(config.numfig_format)
    config.numfig_format = numfig_format


#### Extension setup ##########################################################


def include_static_files(app):
    """
    Copies the static css file required by this extension.
    (Attached to the `builder-inited` Sphinx event.)
    """
    file_path = sphinx_prolog.get_static_path(STATIC_FILE)
    if file_path not in app.config.html_static_path:
        app.config.html_static_path.append(file_path)


def setup(app):
    """
    Sets up the Sphinx extension for the `exercise` and `solution` directives.
    """
    # register the two Sphinx config values used for the extension
    app.add_config_value('sp_exercise_directory', None, 'env')

    # register the custom docutils nodes with Sphinx
    app.add_enumerable_node(
        exercise,
        'exercise',
        exercise_title_getter,
        html=(visit_exercise_node, depart_exercise_node),
        latex=(visit_exercise_node_, depart_exercise_node_),
        text=(visit_exercise_node_, depart_exercise_node_)
    )
    app.add_node(
        exercise_title,
        html=(visit_exercise_title_node, depart_exercise_title_node),
        latex=(visit_exercise_title_node_, depart_exercise_title_node_),
        text=(visit_exercise_title_node_, depart_exercise_title_node_)
    )
    app.add_enumerable_node(
        solution,
        'solution',
        solution_title_getter,
        html=(visit_solution_node, depart_solution_node),
        latex=(visit_solution_node_, depart_solution_node_),
        text=(visit_solution_node_, depart_solution_node_)
    )
    app.add_node(
        solution_title,
        html=(visit_solution_title_node, depart_solution_title_node),
        latex=(visit_solution_title_node_, depart_solution_title_node_),
        text=(visit_solution_title_node_, depart_solution_title_node_)
    )

    # ensure the required auxiliary files are included in the Sphinx build
    app.connect('builder-inited', include_static_files)
    if not sphinx_prolog.is_css_registered(app, STATIC_FILE):
        app.add_css_file(STATIC_FILE)

    # register the custom directives with Sphinx
    app.add_directive('exercise', Exercise)
    app.add_directive('solution', Solution)

    # connect custom hooks to the Sphinx build process
    app.connect('config-inited', set_exercise_numfig_format)
    app.connect('config-inited', set_solution_numfig_format)

    return {'version': sphinx_prolog.VERSION}
