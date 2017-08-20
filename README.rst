=====
Taggy
=====

Command line utility to help create SemVer git tags.

----


Installation
------------

Requires Python >3.4::

    λ pip install taggy


Basic Usage 
-----------

To get help:::

    λ taggy --help      

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


In any git repository type:::

    λ taggy [major/minor/patch]      


If the version bump positional argument is omitted an input prompt will appear:::

    λ taggy       
    Choose: [M]ajor/[m]inor/[p]atch: 


To create a new git tag representing a patch:::

    λ taggy patch


To preview a given action:::

    λ taggy major --preview
    - 1.1.1
    + 2.0.0


To find and replace existing tags within files:::
    
    λ taggy minor [--files/-f] setup.py docs/conf.py


To write a custom message:::

    λ taggy minor [--message/-m] "My tag: {}"
