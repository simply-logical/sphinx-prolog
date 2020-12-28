# :open_book: Simply Logical extensions for Jupyter Book (Sphinx) #

This repository holds a collection of [Sphinx] extensions designed for the
[Jupyter Book] platform.
It implements the following functionality:

* **information boxes** -- admonition-like blocks with *title* and *content*;
* **exercise and solution boxes** -- *numbered* admonition-like blocks holding
  *exercises* and their *solutions*; and
* **interactive Prolog code blocks** -- [SWI Prolog] code blocks that can be
  executed directly in the browser with [SWISH].

> This *readme* file uses [Jupyter Book]'s [MyST Markdown] syntax for **roles**
  and **directives** -- see [MyST overview] for more details.
  For use with [Sphinx], please refer to the [reStructuredText] syntax.

## :information_source: Infobox directive ##

The [`infobox.py`](infobox.py) module defines the `infobox` directive used for
building *information boxes*.

### Usage ###

An *information box* is included with the `infobox` directive:

````text
```{infobox}
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

The `infobox` directive has one **required** parameter:

* `title` -- specifies the title of the information box.

The `infobox` directive also requires a non-empty content.

## :trophy: Exercise and Solution directives ##

The [`solex.py`](solex.py) module defines the `exercise` and `solution`
directives used for building **numbered** *exercise* and *solution* boxes.
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

* `sl_exercise_directory` -- defines the path to a directory holding files with
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
`sl_exercise_directory` configuration parameter.
The exercise file name is expected to be the exercise id without the `ex:`
prefix and with the `.md` extension.
For example, for an exercise with `ex:my_exercise` id, the content file should
be named `my_exercise.md`.
If both the exercise content file exist and the directive is explicitly filled
with content, the latter takes precedent.
Solutions behave in the same way -- their content is sourced from the
**linked exercise file** or is provided directly within the directive.

The `solex` [Sphinx] extension *monitors* the exercise content files for
changes and automatically regenerates the affected pages.

## :floppy_disk: SWISH directive ##

The [`swish.py`](swish.py) module defines the `swish` directive used for
building *interactive [SWI Prolog] boxes* executed directly in the browser with
[SWISH].

### Usage ###

A *[SWISH] box* is included with the `swish` directive:

````text
```{swish} 1.2.3
---
inherit-id: 4.5.6, 4.5.7, 4.5.8
source-text-start: 4.5.6-start
source-text-end: 4.5.6-end
---
```
````

### Configuration parameters ###

The `swish` extension uses the following [Sphinx] configuration parameters:

* `sl_code_directory` (**required**) -- defines the path to a directory holding
  files with content ([SWI Prolog] code) of each [SWISH] code box; and
* `sl_swish_url` -- specifies the URL of the [SWISH] execution server
  (`https://swish.simply-logical.space/` by default, which is hardcoded in the
  the Simply Logical SWISH JavaScript `lpn.js`).

### Arguments, parameters and content ###

Each [SWISH] code box has one **required** argument that
specifies the *unique* id of this particular interactive code block.
The content of the [SWISH] box directive **must be empty** as it is pulled from
a code file whose name is derived from the code box id and which should be
located in the directory specified via the `sl_code_directory` configuration
parameter.
The code file name is expected to be the code block id with `.pl` extension.
For example, for a code block with `my_code` id, the code file should be named
`my_code.pl`.
The `swish` [Sphinx] extension *monitors* the code files for
changes and automatically regenerates the affected pages.

[SWISH] code blocks also have a number of **optional** parameters:

* `inherit-id` -- specifies **id(s)** of code block(s) whose content will be
  inherited into this particular [SWISH] box. The inherited code block(s)
  **must** be placed on the same page (the same document) as the code block
  that inherits them.
  A [SWISH] box can inherit from a single (e.g., `inherit-id: 4.5.6`) or
  multiple (e.g., `inherit-id: 4.5.6, 4.5.7, 4.5.8`) code blocks.
  (The inheritance logic is handled by the `lpn.js` JavaScript.)
* `source-text-start` -- specifies the code **file name** without the `.pl`
  extension whose content will be (implicitly) prepended to the main code of
  this code block (e.g., `source-text-start: 4.5.6-start`).
  (The prefix logic is handled by the `lpn.js` JavaScript.)
* `source-text-end` -- specifies the code **file name** without the `.pl`
  extension whose content will be (implicitly) appended to the main code of
  this code block (e.g., `source-text-end: 4.5.6-end`).
  (The suffix logic is handled by the `lpn.js` JavaScript.)

## TODO ##

- [ ] TODO(Kacper): highlight the paragraph marker for exercise and solution
  boxes when hovering the mouse over the box and not just the character

- [ ] TODO(Kacper): exercise are referenced by `ex:xxx` and solutions by
  `sol:xxx`, but SWISH boxes use the filename without any prefix (reference
  with `swish:...` instead) -- we need consistency (same applies to infoboxes,
  which need `ibox:my-tag`)
- [ ] TODO(Kacper): add a SWISH box parameter to manually include SWISH queries
- [ ] TODO(Kacper): add SWISH queries, both inline and display
- [ ] TODO(Kacper): add a SWISH box parameter to reference an existing query
- [ ] TODO(Kacper): SWISH box content can append or overwrite displayed?
- [ ] TODO(Kacper): add code syntax highlight to SWISH boxes

- [ ] TODO(Kacper): some of the footnotes have messed up numbering (check
  GitHub issues)
- [ ] TODO(Kacper): fix TODO tags
- [ ] TODO(Kacper): hacked named paragraphs (search for `&nbsp;`) into markdown
  sections (e.g., 1.2.1) -- will show up on the right in the content
    - [ ] TODO (Kacper) prevent sphinx from numbering these entries (toc
      `:maxdepth:`, e.g., `maxdepth: 2`) -- see
      [here](https://github.com/executablebooks/jupyter-book/blob/master/jupyter_book/toc.py)

[sphinx]: https://www.sphinx-doc.org/
[jupyter book]: https://jupyterbook.org/
[swish]: https://swish.swi-prolog.org/
[swi prolog]: https://www.swi-prolog.org/
[myst markdown]: https://myst-parser.readthedocs.io/
[reStructuredText]: https://docutils.sourceforge.io/rst.html
[myst overview]: https://jupyterbook.org/content/myst.html
