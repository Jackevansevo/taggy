=====
Taggy
=====

Command line utility to help create SemVer git tags.

----

.. raw:: html

    <a href="https://asciinema.org/a/127416" target="_blank"><img src="https://asciinema.org/a/127416.png" /></a>

----

For those of us too lazy to repeatedly type:

.. code-block:: bash

    ❯ git describe

Followed by:

.. code-block:: bash

    ❯ git tag -a "x.y.z" -m "blah lah blah"

Then having to update package metadata within projects files. Either inside a
text editor or on the command line:

.. code-block:: bash

    ❯ sed -ie "s/0\.0\.1/0.0.2/g" setup.py


Often people cook up shell scripts per project to automate the tagging process.
This tool is an attempt at something project agnostic.


Installation
------------

Requires Python >3.4 (setuptools.run)

.. code-block:: bash

        pip install taggy


Basic Usage 
-----------

To get help:

.. code-block:: none

    ❯ taggy --help      

    usage: taggy [-h] [--preview] [--files [FILES [FILES ...]]]
                 [--message MESSAGE]
                 [{major,minor,patch}]

    Command line utility to help create SemVer git tags.

    positional arguments:
      {major,minor,patch}

    optional arguments:
      -h, --help            show this help message and exit
      --preview
      --files [FILES [FILES ...]], -f [FILES [FILES ...]]
      --message MESSAGE, -m MESSAGE


In any git repository type:

.. code-block:: bash

    ❯ taggy [major/minor/patch]      


If the version bump positional argument is omitted an input prompt will appear:

.. code-block:: bash

    ❯ taggy       
    Choose: [M]ajor/[m]inor/[p]atch: 


To create a new git tag representing a patch:

.. code-block:: bash

    ❯ taggy patch


To preview a given action:

.. code-block:: bash

    ❯ taggy major --preview
    - 1.1.1
    + 2.0.0


To find and replace existing tags within files:
    
.. code-block:: bash

    ❯ taggy minor [--files/-f] setup.py docs/conf.py


To write a custom message:

.. code-block:: bash

    ❯ taggy minor [--message/-m] "My tag: {}"


FAQ
---

* Why only support Python >3.4

  * because it's <CURRENT YEAR>

* Where are the tests?

  * Coming soon

* Can you make it support X?

  * Open and issue and I'll do my best, or submit a PR


TODO
----
- Tests
- Continuous Integration
- Install instructions
- Documentation
- Demo screencast (needs redoing)
- File globs for find and replace
- Find and replace sed preview
