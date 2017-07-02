#! /usr/bin/env python

import argparse
import os
import sys
from difflib import ndiff
from itertools import chain
from re import escape
from shutil import which
from subprocess import DEVNULL, PIPE, CalledProcessError, run
from typing import Optional

from semver import bump_major, bump_minor, bump_patch  # type: ignore

DESC = 'Command line utility to help create SemVer tags.'


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=DESC)
    parser.add_argument('--preview', action="store_true")
    parser.add_argument('files', type=argparse.FileType('r'), nargs='*')
    bump = parser.add_mutually_exclusive_group()
    bump.add_argument('--major', '-M', action="store_true")
    bump.add_argument('--minor', '-m', action="store_true")
    bump.add_argument('--patch', '-p', action="store_true")
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


def create_tag(path: str, tag):
    message = f'my version {tag}'
    cmd = ['git', 'tag', '-a', tag, '-m', message]
    result = run(cmd, cwd=path)
    return result


def find_and_replace(path, old, new, files):
    sed_regex = 's/{}/{}/g'.format(escape(old), new)
    cmd = chain(['sed', '-i', '-e', sed_regex], [f.name for f in files])
    result = run(cmd, cwd=path)
    return result


def choice(question, choices, retry=True, lower=False):
    try:
        selected = input(question).lower() if lower else input(question)
    except (KeyboardInterrupt, EOFError):
        sys.exit("\nInterrupted, quitting")
    else:
        if selected not in choices:
            return choice(question, choices) if retry else selected
        return selected


def confirm(question):
    text = ' '.join([question, '[Y/n]: '])
    return choice(text, ['y', 'n', 'yes', 'no'], lower=True) in ('yes', 'y')


def main():

    # Immediately Bail if git isn't found
    if not which('git'):
        print('git executable not found on current $PATH\n Exiting')
        sys.exit(1)

    # Get directory from where script was called
    cwd = os.getcwd()

    # Checks if cwd is a git repository
    if not is_git_repo(cwd):
        print('Error: {} Not a git repository\n'.format(cwd))
        if confirm('Initialize git repositroy?'):
            run(['git', 'init'])
        sys.exit(1)

    # Parse command line arguments
    args = get_args()

    # Acquire current git tag
    tag = get_tag(cwd)

    if tag is None:
        if confirm('No tags found, create initial tag: "0.1.0"'):
            create_tag(cwd, '0.1.0')
        sys.exit()

    short_flags = ('M', 'm', 'p')
    options = ('major', 'minor', 'patch')

    # Check if argparse was passed a version bump flag
    if not any(getattr(args, x) for x in options):
        selected = choice('Choose: [M]ajor/[m]inor/[p]atch: ', ['M', 'm', 'p'])
        bump = dict(zip(short_flags, options)).get(selected)
    else:
        bump = next(iter(arg for arg in options if getattr(args, arg)))

    bump_fns = {'major': bump_major, 'minor': bump_minor, 'patch': bump_patch}
    next_tag = bump_fns[bump](tag)

    # If it's only a preview, exit
    if args.preview:
        old, new = ('{}\n'.format(v) for v in (tag, next_tag))
        print(''.join(ndiff([old], [new])), end="")
        sys.exit(0)

    result = create_tag(cwd, next_tag)
    if result.returncode == 0:
        print('Created new tag: {} successfully'.format(next_tag))

    if args.files:
        find_and_replace(cwd, tag, next_tag, args.files)
