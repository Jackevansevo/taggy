#!/usr/bin/env python
# -*- coding: utf-8 -*-

from itertools import chain
from setuptools import setup, find_packages
from taggy import __version__

dev_requirements = [
    'flake8',
    'isort',
    'mypy',
]

test_requirements = [
    'pytest',
    'pytest-cov',
]


setup(
    name='taggy',
    version=__version__,
    description='Command line utility to help create SemVer tags.',
    url='https://github.com/Jackevansevo/taggy',
    author='Jack Evans',
    author_email='jack@evans.gb.net',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    packages=['taggy'],
    setup_requires=['pytest-runner'],
    tests_require=test_requirements,
    install_requires=['crayons'],
    python_requires='>=3.4',
    entry_points={
        'console_scripts': [
            'taggy=taggy.cli:main'
        ]
    },
    extras_require={
        'dev': list(chain(dev_requirements, test_requirements)),
        'test': test_requirements,
    },
)
