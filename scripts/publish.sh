#!/bin/sh -e

export PREFIX=""
if [ -d 'venv' ] ; then
    export PREFIX="venv/bin/"
fi

export VERSION=`${PREFIX}python setup.py --version`


find taggy -type f -name "*.py[co]" -delete
find taggy -type d -name __pycache__ -delete

${PREFIX}python setup.py sdist
${PREFIX}twine upload dist/*

rm -rf dist
rm -rf taggy.egg-info
