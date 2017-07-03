from taggy import __version__
from setuptools import setup

setup(
    name='taggy',
    description='Command line utility to help create SemVer tags.',
    version=__version__,
    py_modules=['taggy'],
    author_email='jack@evans.gb.net',
    license='MIT',
    url='https://github.com/Jackevansevo/taggy',
    install_requires=['semver'],
    entry_points={'console_scripts': ['taggy=taggy.cli:main']},
    zip_safe=False,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    keywords='semver git tag',
    python_requires='>=3.5',
)
