=====
Taggy
=====

Command line utility to help create SemVer tags.

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
    usage: taggy [-h] [--preview] [--major | --minor | --patch]
                 [files [files ...]]

    Command line utility to help create SemVer tags.

    positional arguments:
      files

    optional arguments:
      -h, --help   show this help message and exit
      --preview
      --major, -M
      --minor, -m
      --patch, -p


In any git repository type:

.. code-block:: bash

    ❯ taggy -[M/m/p]      


If the version bump flag is omitted an input prompt will appear:

.. code-block:: bash

    ❯ taggy       
    Choose: [M]ajor/[m]inor/[p]atch: 


To create a new git tag representing a patch:

.. code-block:: bash

    ❯ taggy -p


To preview a given action:

.. code-block:: bash

    ❯ taggy -M --preview
    - 1.1.1
    + 2.0.0


FAQ
---

- Why only support Python >3.4
  - because it's <CURRENT YEAR>
- Where are the tests?
  - Non existent (so far)
- Can you make it support X?
  - Open an issue / PR


TODO
----
- Tests
- Continuous Integration
- Install instructions
- Documentation
- Demo screencast
- File globs for find and replace
- Find and replace sed preview
- Handle prefixes better
