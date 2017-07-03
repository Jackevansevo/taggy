#! /usr/bin/env python

import os
import string
import sys
from argparse import ArgumentParser, FileType, Namespace
from difflib import ndiff
from itertools import chain
from re import escape
from shutil import which
from subprocess import DEVNULL, PIPE, CalledProcessError, run
from typing import Optional, Tuple

from semver import bump_major, bump_minor, bump_patch  # type: ignore

DESC = 'Command line utility to help create SemVer git tags.'

# SemVer numeric conventions
SEMVER_NUMS = ('major', 'minor', 'patch')

# Slice constants
PREFIX = slice(0, 1)
REST = slice(1, None)


# [TODO]
# - Preview sed find and replace, (use temp files, then diff)

def get_args() -> Namespace:
    parser = ArgumentParser(description=DESC)
    parser.add_argument('bump', type=str.lower, nargs='?', choices=SEMVER_NUMS)
    parser.add_argument('--preview', action="store_true")
    parser.add_argument('--files', '-f', type=FileType('r'), nargs='*')
    parser.add_argument('--message', '-m', type=str, default="version {}")
    return parser.parse_args()


def is_git_repo(path: str) -> bool:
    cmd = ['git', 'rev-parse']
    code = run(cmd, cwd=path, stdout=DEVNULL, stderr=DEVNULL).returncode
    return code == 0


def sanitize(s) -> str:
    return s.decode('utf-8').strip()


def get_tag(path: str, default=None) -> Optional[str]:
    # Try and describe the current repository
    cmd = ['git', 'describe', '--abbrev=0']
    try:
        # Capture stdout, discard stderr
        result = run(cmd, stdout=PIPE, stderr=DEVNULL, cwd=path, check=True)
    except CalledProcessError:
        # Return default value if exit code is non zero
        return default
    else:
        return sanitize(result.stdout)


def create_tag(path: str, tag, message):
    cmd = ['git', 'tag', '-a', tag, '-m', message.format(tag)]
    result = run(cmd, cwd=path)
    return result


def find_and_replace(path, old, new, files):
    sed_regex = 's/{}/{}/g'.format(escape(old), new)
    cmd = chain(['sed', '-i', '-e', sed_regex], [f.name for f in files])
    result = run(cmd, cwd=path)
    return result


def prompt(question, lower=False, quit=True):
    try:
        answer = input(question)
    except (KeyboardInterrupt, EOFError) as error:
        if quit:
            sys.exit("\nInterrupted, quitting")
        else:
            raise error
    else:
        return answer.lower() if lower else answer


def unique_prefixes(strings) -> bool:
    return len({s[PREFIX].lower() for s in strings}) == len(strings)


def prefix_choice(question, choices, retry=True):
    # [TODO] Use smart case sensivity,
    # e.g. with options [M]ajor/[m]inor/[p]atch:
    # 'p' needs to be case insensivite since it's the only 'p' character prefix
    prefixes = {choice[PREFIX]: choice for choice in choices}
    # Lower cases user input if choices all have unique lower case prefixes
    selected = prompt(question, lower=unique_prefixes(choices))
    if len(selected) == 1 and selected in prefixes:
        return prefixes.get(selected)
    if selected not in choices:
        return prefix_choice(question, choices, retry) if retry else selected
    return selected


def strip_prefix(tag) -> Tuple[Optional[str], str]:
    if tag.startswith(tuple(string.ascii_letters)):
        return (tag[PREFIX], tag[REST])
    return (None, tag)


def confirm(question):
    text = ' '.join([question, '[Y/n]: '])
    return prefix_choice(text, ('yes', 'no')).lower() == 'yes'


def runchecks(cwd):
    # Immediately Bail if git isn't found
    if not which('git'):
        print('git executable not found on current $PATH\n Exiting')
        sys.exit(1)

    # Checks if cwd is a git repository
    if not is_git_repo(cwd):
        print('Error: {} Not a git repository\n'.format(cwd))
        if confirm('Initialize git repositroy?'):
            run(['git', 'init'])
        sys.exit(1)


def main():

    # Get directory from where script was called
    cwd = os.getcwd()

    # Validate current environment before proceeding
    runchecks(cwd)

    # Parse command line arguments
    args = get_args()

    # Acquire current git tag
    tag = get_tag(cwd)

    if tag is None:
        if confirm('No tags found, create initial tag: "0.1.0"'):
            create_tag(cwd, '0.1.0', args.message)
        sys.exit()

    # Strip prefix from tag, "v1.2.3" is not a semantic version
    # But it's a common way to indiciate a version number in version control
    prefix, tag = strip_prefix(tag)

    if args.bump is None:
        question = 'Choose: [M]ajor/[m]inor/[p]atch: '
        choices = ('Major', 'minor', 'patch')
        args.bump = prefix_choice(question, choices).lower()

    bump_fns = {'major': bump_major, 'minor': bump_minor, 'patch': bump_patch}
    next_tag = bump_fns[args.bump](tag)

    # If previous tag had a prefix, rejoin the prefix after bumping
    if prefix is not None:
        next_tag = prefix + next_tag

    # If it's only a preview, exit
    if args.preview:
        old, new = ('{}\n'.format(v) for v in (tag, next_tag))
        print(''.join(ndiff([old], [new])), end="")
        sys.exit(0)

    # Find & replace SemVer tag inside files (ignoring prefix)
    if args.files:
        _, new_tag = strip_prefix(next_tag)
        find_and_replace(cwd, tag, new_tag, args.files)

    result = create_tag(cwd, next_tag, args.message)
    if result.returncode == 0:
        print('Created new tag: {} successfully'.format(next_tag))
