[![Licence][licence-badge]][licence-link]
[![Python][python-badge]][python-link]
[![PyPI][pypi-badge]][pypi-link]
[![Documentation][doc-badge]][doc-link]

[licence-badge]: https://img.shields.io/github/license/simply-logical/sphinx-prolog.svg
[licence-link]: https://github.com/simply-logical/sphinx-prolog/blob/master/LICENCE
[python-badge]: https://img.shields.io/badge/python-3.5-blue.svg
[python-link]: https://github.com/simply-logical/sphinx-prolog
[pypi-badge]: https://img.shields.io/pypi/v/sphinx-prolog.svg
[pypi-link]: https://pypi.org/project/sphinx-prolog
[doc-badge]: https://img.shields.io/badge/read-documentation-blue.svg
[doc-link]: https://book-template.simply-logical.space

# :open_book: Simply Logical extensions for Jupyter Book (Sphinx) #

This repository holds a collection of [Sphinx] extensions designed for the
[Jupyter Book] platform.
It implements the following functionality:

* **information boxes** -- admonition-like blocks with *title* and *content*;
* **exercise and solution boxes** -- *numbered* admonition-like blocks holding
  *exercises* and their *solutions*; and
* **interactive Prolog code blocks** -- [SWI Prolog] code blocks that can be
  executed directly in the browser with [SWISH].

**This readme file holds a technical documentation of the `sphinx-prolog`
extension.
We also publish a [Jupyter Book] template for authoring interactive Prolog
content that simultaneously serves as a _user guide_ to the functionality
implemented by this extension.
The template is available in the [simply-logical/prolog-book-template] GitHub
repository and the built guide can be found at
<https://book-template.simply-logical.space/>;
the "`sphinx-prolog` Extension" section should be of particular interest.**

> This *readme* file uses [Jupyter Book]'s [MyST Markdown] syntax for **roles**
  and **directives** -- see [MyST overview] for more details.
  For use with [Sphinx], please refer to the [reStructuredText] syntax.

---

To get started with `sphinx-prolog`, first install it with `pip`:
```bash
pip install sphinx-prolog
```
then, add desired `sphinx_prolog` extensions to the Sphinx `extensions` list
in your `conf.py`
```Python
...
extensions = ['sphinx_prolog.infobox',
              'sphinx_prolog.solex',
              'sphinx_prolog.swish',
              'sphinx_prolog.pprolog',
              ]
...
```

## :information_source: Infobox directive ##

The [`sphinx_prolog.infobox`](sphinx_prolog/infobox.py) module defines the
`infobox` directive used for building *information boxes*.

### Usage ###

An *information box* is included with the `infobox` directive:

````text
```{infobox} ibox:4.2
---
title: Title of my infobox
---
Content of my information box.
```
````

> Note that if the content of an information box includes directives
  introduced with a **triple** backtick, the `infobox` directive itself should
  be introduced with a **quadruple** backtick.
  This logic applies to all nested directives.

### Arguments, parameters and content ###

The `infobox` directive has one **optional** argument that specifies the
referenceable label of this box.
The label must be prefixed with `ibox:`.
Then, the box can be referenced with the standard `ref` role, e.g.,
`` {ref}`ibox:4.2` ``, which will produce a hyper-link with the title of the
information box.

Additionally, the `infobox` directive has one **required** parameter:

* `title` -- specifies the title of the information box.

The `infobox` directive also requires a non-empty content.

## :trophy: Exercise and Solution directives ##

The [`sphinx_prolog.solex`](sphinx_prolog/solex.py) module defines the
`exercise` and `solution` directives used for building **numbered** *exercise*
and *solution* boxes.
These elements can be referenced with the standard `ref` and `numref` roles.

### Usage ###

#### Exercise ####

An *exercise box* is included with the `exercise` directive:

````text
```{exercise} ex:2.9
Content of my exercise box.
```
````

Each exercise can be referenced with its name using the `ref` role, e.g.,
`` {ref}`ex:2.9` ``, which produces *exercise* hyper-link;
or with a `numref` role, e.g., `` {numref}`ex:2.9` ``, to get a numbered
hyper-link reference such as *Exercise #*.

> Note that the display text of the hyper-link produced with the `ref` role can
  be altered with the following syntax: `` {ref}`custom hyper-link<ex:2.9>` ``.
  The format string of the numbered reference can also be changed individually
  for each reference using the following syntax:
  `` {numref}`Task %s<ex:2.9>` ``, where `%s` will be replaced with the
  exercise number.
  Alternatively, the format string for the numbered references can be changed
  globally with the corresponding [Sphinx] configuration parameter -- see the
  following section for more details.

#### Solution ####

A *solution box* is included with the `solution` directive:

````text
```{solution} ex:2.9
Content of my solution box.
```
````

Note that each solution **must** be linked to an existing exercise, hence the
`ex:2.9` argument.
This syntax ensures that the solution has the same sequential number as the
underlying exercise.
Similar to exercises, solutions can be referenced with the `ref` and `numref`
roles, with the corresponding hyper-links formatted as *solution* and
*Solution #* respectively.
The reference id of each solution box is generated automatically and derived
from the corresponding exercise id by replacing `ex` with `sol`, e.g., a
solution to an exercise with id `ex:2.9` can be referenced with `sol:2.9`.

### Configuration parameters ###

The `solex` extension uses the following [Sphinx] configuration parameters:

* `sp_exercise_directory` -- defines the path to a directory holding files with
  content of each exercise;
* `numfig_format.exercise` -- defines a custom formatter of the exercise
  `numref` role, e.g., `"Question %s"` where `%s` will be automatically
  replaced with the exercise number (`"Exercise %s"` by default); and
* `numfig_format.solution` -- defines a custom formatter of the solution
  `numref` role, e.g., `"Answer %s"` where `%s` will be automatically replaced
  with the solution number derived from the corresponding exercise
  (`"Solution %s"` by default).

### Arguments, parameters and content ###

Each exercise and solution has one **required** argument that **must** start
with `ex:...` and specifies the *unique* id of this particular exercise.
It is used to link a solution to an exercise and to reference it (the solution
is referenced with the corresponding `sol:...` id, which is generated
automatically).

The content of an exercise or a solution directive **can be empty**, in which
case the `solex` extension looks for a content file whose name is derived from
the exercise id and which should be located in the directory specified with the
`sp_exercise_directory` configuration parameter.
The exercise file name is expected to be the exercise id without the `ex:`
prefix and with the `.md` extension.
For example, for an exercise with `ex:my_exercise` id, the content file should
be named `my_exercise.md`.
If both the exercise content file exist and the directive is explicitly filled
with content, the latter takes precedence.
Solutions behave in the same way -- their content is sourced from the
**linked exercise file** or is provided directly within the directive.

The `solex` [Sphinx] extension *monitors* the exercise content files for
changes and automatically regenerates the affected pages.

## :floppy_disk: SWISH directive ##

The [`sphinx_prolog.swish`](sphinx_prolog/swish.py) module defines the `swish`
and `swish-query` directives, as well as the `swish-query` role, all of which
are used for building *interactive [SWI Prolog] boxes* executed directly in the
browser with [SWISH].

### Usage ###

#### Code box ####

A *[SWISH] code box* is included with the `swish` directive:

````text
```{swish} swish:1.2.3
---
query-text: ?-linked(a,b,X). ?-linked(X,a,Y).
query-id: swishq:1.1.1 swishq:1.1.2 swishq:1.1.3
inherit-id: swish:4.5.6 swish:4.5.7 swish:4.5.8
source-text-start: 4.5.6-start
source-text-end: 4.5.6-end
hide-examples: true
build-file: false
---
optional :- content.
```
````

Each [SWISH] code box can be referenced with its name using the `ref`
role, e.g., `` {ref}`swish:1.2.3` ``, which produces *SWISH code box*
hyper-link.

#### Query box ####

A **display** *[SWISH] query box* is included with the `swish-query`
*directive*:

````text
```{swish-query} swishq:1.2.3
---
source-id: swish:1.0.0 swish:1.0.1 swish:1.0.2
---
?-my_query(a,X).
```
````

An **inline** *[SWISH] query box* is included with the `swish-query` *role*:

```text
{swish-query}`?-my_query(a,X). <swishq:1.2.3>`
```

Each [SWISH] query box can be referenced with its name using the `ref`
role, e.g., `` {ref}`swishq:1.2.3` ``, which produces *SWISH query box*
hyper-link.

### Configuration parameters ###

The `swish` extension uses the following [Sphinx] configuration parameters:

* `sp_code_directory` (**required**) -- defines the path to a directory holding
  files with content ([SWI Prolog] code) of each [SWISH] code box; and
* `sp_swish_url` -- specifies the URL of the [SWISH] execution server
  (`https://swish.swi-prolog.org/` by default, which is hard-coded in the
  Simply Logical SWISH JavaScript
  [`lpn.js`](sphinx_prolog/_static/lpn.js)).
* `sp_swish_hide_examples` (*optional*, default `False`) -- **globally**
  toggles visibility of the `/** <examples> ... */` block in SWISH code boxes.
  This behaviour can also be changed *locally* for each individual code box
  with the `hide-examples` parameter of the `swish` directive (see below).
* `sp_swish_book_url` (**required** when using [SWISH] code boxes with the
  `build-file` parameter set to `true`) -- a *base URL* under which the book
  will be deployed.
  It is used to compose links to Prolog code files that need to be accessed
  by file-based [SWISH] boxes.
  (See the description of the `build-file` parameter for more details.)

### Arguments, parameters and content ###

#### Code box ####

Each [SWISH] code box has one **required** argument that
specifies the *unique* id of this particular interactive code block.
This id **must** start with the `swish:` prefix.
The content of a [SWISH] box can **either** be provided explicitly within the
directive, **or** -- when the content is left empty -- it is pulled from a code
file whose name is derived from the code box id and which should be located in
the directory specified via the `sp_code_directory` configuration parameter.
The code file name is expected to be the code block id **without** the `swish:`
prefix and **with** the `.pl` extension.
For example, for a code block with `swish:my_code` id, the code file should be
named `my_code.pl`.
The `swish` [Sphinx] extension *monitors* the code files for
changes and automatically regenerates the affected pages.

[SWISH] code blocks also have a number of **optional** parameters:

* `query-text` -- specifies a collection of queries to be implicitly embedded
  in the [SWISH] box (handled by the [`lpn.js`](sphinx_prolog/_static/lpn.js)
  JavaScript).
  If both the `/** <examples> ... */` block (in the [SWISH] box content) and
  the `query-text` parameter are provided, the latter takes precedence.
  However, the `query-text` parameter works in conjunction with the
  *code box*'s `query-id` and *query box*'s `source-id` parameters.
* `query-id` -- specifies (space separated) **id(s)** of query block(s) whose
  content will be used to populate the queries of this [SWISH] box
  (handled by the [`lpn.js`](sphinx_prolog/_static/lpn.js) JavaScript).
  A [SWISH] code box can import a single (e.g., `query-id: swishq:4.5.6`) or
  multiple (e.g., `query-id: swishq:4.5.6 swishq:4.5.7 swishq:4.5.8`) query
  blocks.
  Each [SWISH] query box **must** be placed on the same page (the same
  document) as the code block that uses it.
  The `query-id` parameter takes precedence over the `/** <examples> ... */`
  block (in the [SWISH] box content), but it works in conjunction with the
  *code box*'s `query-text` and *query box*'s `source-id` parameters.
* `inherit-id` -- specifies (space separated) **id(s)** of code block(s) whose
  content will be inherited into this particular [SWISH] box.
  The inherited code block(s) **must** be placed on the same page (the same
  document) as the code block that inherits them.
  A [SWISH] box can inherit from a single (e.g., `inherit-id: swish:4.5.6`) or
  multiple (e.g., `inherit-id: swish:4.5.6 swish:4.5.7 swish:4.5.8`) code
  blocks.
  (The inheritance logic is handled by the
  [`lpn.js`](sphinx_prolog/_static/lpn.js) JavaScript.)
* `source-text-start` -- specifies the code **file name** without the `.pl`
  extension whose content will be (implicitly) prepended to the main code of
  this code block (e.g., `source-text-start: 4.5.6-start`).
  (The prefix logic is handled by the [`lpn.js`](sphinx_prolog/_static/lpn.js)
  JavaScript.)
* `source-text-end` -- specifies the code **file name** without the `.pl`
  extension whose content will be (implicitly) appended to the main code of
  this code block (e.g., `source-text-end: 4.5.6-end`).
  (The suffix logic is handled by the [`lpn.js`](sphinx_prolog/_static/lpn.js)
  JavaScript.)
* `hide-examples` (*not set*, `true` or `false`) -- prevents the
  `/** <examples> ... */` block from being displayed (when not set, it is
  controlled by the `sp_swish_hide_examples` configuration parameter).
* `build-file` (*not set*, `true` or `false`) -- long Prolog scripts cannot be
  loaded into [SWISH] boxes since URL requests have 2048 character limit.
  To allow for long Prolog scripts, all of the relevant code fragments are
  processed by this Python extension and placed in a single Prolog file.
  This file is then loaded into a [SWISH] box by its URL, which is composed
  from the book deployment URL provided by the user via the `sp_swish_book_url`
  configuration parameter and the Prolog script storage directory
  (`_sources/prolog_build_files/...`).
  The built Prolog files are stored under `src/code/temp` and then copied to
  the target directory (`_sources/prolog_build_files` located, for example,
  under `_build/html` for *html* builds) -- you may need to explicitly exclude
  this path in the Sphinx configuration file by adding it to
  `exclude_patterns`.
  This functionality has to be **explicitly** enabled by setting the
  `build-file` parameter to `true`.
  **Note: such [SWISH] boxes will not work when browsing local
  documentation/book builds since the code files must be hosted on a server
  accessible by [SWISH].**

#### Query box ####

Each [SWISH] query *directive* has one **required** argument that
specifies the *unique* id of this particular query block (which can be
referenced by the `query-id` parameter of the [SWISH] code boxes).
This id **must** start with the `swishq:` prefix.
Similar, `swish-query` *roles* must contain their unique ids placed at the end
of the role text and wrapped within angle brackets, e.g.,
`` {swish-query}`?-my_prolog_query(a, B). <swishq:my_id>` ``.

Additionally, the [SWISH] query block **directive** has one **optional**
parameter:

* `source-id` -- specifies (space separated) **id(s)** of code block(s) that
  will be injected with this particular query (handled by the
  [`lpn.js`](sphinx_prolog/_static/lpn.js) JavaScript).
  A [SWISH] query box can indicate a single (e.g., `source-id: swish:1.0.0`) or
  multiple (e.g., `source-id: swish:1.0.0 swish:1.0.1 swish:1.0.2`) code
  blocks.
  Each referenced [SWISH] code box **must** be placed on the same page (the
  same document) as the query box.
  The `source-id` parameter takes precedence over the `/** <examples> ... */`
  block (in the [SWISH] box content), but it works in conjunction with the
  `query-id` and `query-text` parameters of the [SWISH] code blocks.

## :test_tube: pseudo Prolog syntax highlighting ##

The [`sphinx_prolog.pprolog`](sphinx_prolog/pprolog.py) module defines code
block syntax highlighting for *pseudo Prolog* (`pProlog`).

### Usage ###

A *pseudo Prolog* (`pProlog`) code box with appropriate syntax highlighting is
included with the standard *backtick fence* syntax (` ``` `) indicating
`pProlog` programming language:

````
```pProlog
my,pseudo,prolog;-code.
```
````

---

> The CSS and JS files used by this [Sphinx] extension (namely
  [`sphinx-prolog.css`](sphinx_prolog/_static/sphinx-prolog.css),
  [`lpn.css`](sphinx_prolog/_static/lpn.css) and
  [`lpn.js`](sphinx_prolog/_static/lpn.js), as well as their dependencies
  [`jquery-ui.min.css`](sphinx_prolog/_static/jquery-ui.min.css) and
  [`jquery-ui.min.js`](sphinx_prolog/_static/jquery-ui.min.js),
  and their auxiliary files
  [`lpn-run.png`](sphinx_prolog/_static/lpn/lpn-run.png) and
  [`lpn-close.png`](sphinx_prolog/_static/lpn/lpn-close.png))
  can be found in the [`sphinx_prolog/_static`](sphinx_prolog/_static)
  directory of this repository.

[sphinx]: https://www.sphinx-doc.org/
[jupyter book]: https://jupyterbook.org/
[swish]: https://swish.swi-prolog.org/
[swi prolog]: https://www.swi-prolog.org/
[myst markdown]: https://myst-parser.readthedocs.io/
[reStructuredText]: https://docutils.sourceforge.io/rst.html
[myst overview]: https://jupyterbook.org/content/myst.html
[simply-logical/simply-logical]: https://github.com/simply-logical/simply-logical
[simply-logical/prolog-book-template]: https://github.com/simply-logical/prolog-book-template
