# Copyright (C) 2020
# Author: Kacper Sokol <k.sokol@bristol.ac.uk>
# License: new BSD
"""
Implements the `infobox` directive for Jupyter Book and Sphinx.
"""

from docutils import nodes
from docutils.parsers.rst import Directive, directives

from sl import VERSION

#### Infobox directive ########################################################


class infobox_title(nodes.title):
    """A `docutils` node holding the **title** of Simply Logical infoboxes."""


def visit_infobox_title_node(self, node):
    """
    Builds an opening HTML tag for the **title** node of the Simply Logical
    infoboxes.

    Overrides Sphinx's HTML5
    `visit title <https://github.com/sphinx-doc/sphinx/blob/68cc0f7e94f360a2c62ebcb761f8096e04ebf07f/sphinx/writers/html5.py#L355>`_.
    """
    assert self.builder.name != 'singlehtml', (
        'This function is not suitable for singlehtml builds -- '
        'see the URL in the docstring.')
    if not isinstance(node, infobox_title):
        raise RuntimeError('This function should only be used to process '
                           'an infobox title.')
    if not isinstance(node.parent, infobox):
        raise RuntimeError('This function should only be used to process '
                           'an infobox title that is embedded within an '
                           'infobox node.')
    assert len(node.parent['ids']) == 1, (
        'Infobox nodes need to be ided to be referenceable.')

    self.visit_title(node)


def depart_infobox_title_node(self, node):
    """
    Builds a closing HTML tag for the **title** node of the Simply Logical
    infoboxes.

    Overrides `Sphinx's HTML5 generator <https://github.com/sphinx-doc/sphinx/blob/68cc0f7e94f360a2c62ebcb761f8096e04ebf07f/sphinx/writers/html5.py#L362>`_.
    """
    if (self.permalink_text and self.builder.add_permalinks
            and node.parent.hasattr('ids') and node.parent['ids']):
        self.add_permalink_ref(node.parent, 'Permalink to this infobox')
    else:
        raise RuntimeError('Could not add a permalink to an infobox.')

    self.depart_title(node)


def visit_infobox_title_node_(self, node):
    """
    Builds a prefix for embedding the **title** of Simply Logical infoboxes in
    LaTeX and raw text.
    """
    raise NotImplemented


def depart_infobox_title_node_(self, node):
    """
    Builds a postfix for embedding the **title** of Simply Logical infoboxes in
    LaTeX and raw text.
    """
    raise NotImplemented


class infobox(nodes.Admonition, nodes.Element):
    """A `docutils` node holding Simply Logical infoboxes."""


def visit_infobox_node(self, node):
    """
    Builds an opening HTML tag for Simply Logical infoboxes.

    Overrides `Sphinx's HTML5 generator <https://github.com/sphinx-doc/sphinx/blob/3.x/sphinx/writers/html5.py#L53>`_.
    """
    self.body.append(self.starttag(
        node, 'div', CLASS=('admonition infobox')))


def depart_infobox_node(self, node):
    """
    Builds a closing HTML tag for Simply Logical infoboxes.

    Overrides `Sphinx's HTML5 generator <https://github.com/sphinx-doc/sphinx/blob/3.x/sphinx/writers/html5.py#L53>`_.
    """
    self.body.append('</div>\n')


def visit_infobox_node_(self, node):
    """
    Builds a prefix for embedding Simply Logical infoboxes in LaTeX and raw
    text.
    """
    raise NotImplemented
    self.visit_admonition(node)


def depart_infobox_node_(self, node):
    """
    Builds a postfix for embedding Simply Logical infoboxes in LaTeX and raw
    text.
    """
    raise NotImplemented
    self.depart_admonition(node)


class Infobox(Directive):
    """
    Defines the `infobox` directive for building Simply Logical infoboxes.

    The `infobox` directive is of the form::
       .. infobox::
         :title: Infobox title (required)

         Infobox content.
    """
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = False
    has_content = True
    option_spec = {'title': directives.unchanged}

    def run(self):
        """Builds an infobox."""
        env = self.state.document.settings.env
        # get the directive options
        options = self.options

        # get a custom target node for linking with HTML ids
        targetid = 'infobox-{:d}'.format(env.new_serialno('infobox'))
        targetnode = nodes.target('', '', ids=[targetid])

        # build an infobox node
        infobox_content_node = infobox('\n'.join(self.content))

        # try to get the title -- it is a required argument
        infobox_title_ = options.get('title', None)
        if infobox_title_ is None:
            raise KeyError('infobox directive: the *title* option is missing.')
        infobox_title_node = infobox_title(infobox_title_)

        # a hack to process the title, extract it and embed it in the title
        # node
        parsed_infobox_title = nodes.TextElement()
        self.state.nested_parse(
            [infobox_title_], 0, parsed_infobox_title)
        assert len(parsed_infobox_title.children) == 1
        for child in parsed_infobox_title.children[0]:
            infobox_title_node += child

        # append the title node and process the content node
        infobox_content_node += infobox_title_node
        self.state.nested_parse(
            self.content, self.content_offset, infobox_content_node)

        return [targetnode, infobox_content_node]


#### Extension setup ##########################################################


def setup(app):
    """
    Sets up the Sphinx extension for the `infobox` directive.
    """
    # register the custom docutils nodes with Sphinx
    app.add_node(
        infobox,
        html=(visit_infobox_node, depart_infobox_node),
        latex=(visit_infobox_node_, depart_infobox_node_),
        text=(visit_infobox_node_, depart_infobox_node_)
    )
    app.add_node(
        infobox_title,
        html=(visit_infobox_title_node, depart_infobox_title_node),
        latex=(visit_infobox_title_node_, depart_infobox_title_node_),
        text=(visit_infobox_title_node_, depart_infobox_title_node_)
    )

    # ensure the required auxiliary files are included in the Sphinx build
    if 'jupyter_book' not in app.config.extensions:
        # Jupyter Books takes care of it
        app.add_css_file('sl.css')

    # register the custom directives with Sphinx
    app.add_directive('infobox', Infobox)

    return {'version': VERSION}
