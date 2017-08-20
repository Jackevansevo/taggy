#!/usr/bin/env python

import os
import string
import sys
from argparse import ArgumentParser, FileType, Namespace
from difflib import ndiff, unified_diff
from os import fdopen, remove
from shutil import copy, which
from subprocess import DEVNULL, PIPE, CalledProcessError, run
from tempfile import mkstemp
from typing import Optional, Tuple

import crayons  # type: ignore
from taggy import __version__
from taggy.prompts import choice, confirm
from taggy.semver import Semver

DESC = 'Command line utility to help create SemVer git tags.'

# SemVer numeric conventions
SEMVER_NUMS = ('major', 'minor', 'patch')

# Slice constants
PREFIX = slice(0, 1)
REST = slice(1, None)


def parse_args(args) -> Namespace:
    parser = ArgumentParser(description=DESC, )
    parser.add_argument('bump', type=str.lower, nargs='?', choices=SEMVER_NUMS)
    parser.add_argument(
        '--preview', '-p', action='store_true',
        help='Display a preview of changes'
    )
    parser.add_argument(
        '--no-tag', '-n', action='store_true',
        help='Prevents git from creating new tags'
    )
    parser.add_argument(
        '--yes', '-y', action='store_true',
        help='Auto confirms all confirmation prompts'
    )
    parser.add_argument(
        '--message', '-m', type=str, metavar='', default='version {}',
        help='Message for tag annotation'
    )
    parser.add_argument(
        '--version', action='store_true',
        help='shows currently installed version'
    )
    parser.add_argument(
        '--no-color', action='store_true', help='disables coloured output'
    )
    parser.add_argument(
        '--files', '-f', type=FileType('r'), nargs='*',
        help='list of file names to find and replace version number'
    )
    args = parser.parse_args(args)
    if args.no_tag and args.files is None:
        parser.error('--files are required when --no-tag is set')

    # Disable all colour if flags are present
    if args.no_color:
        crayons.disable()

    # Handle version flag
    if args.version:
        print("Current version:", __version__)
        sys.exit(0)

    return args


def is_git_repo(path: str) -> bool:
    """Returns True if path is a git repository"""
    cmd = ['git', 'rev-parse']
    out = run(cmd, cwd=path, stdout=DEVNULL, stderr=DEVNULL)
    return out.returncode == 0


def sanitize(s) -> str:
    """
    Returns string decoded from utf-8 with leading/trailing whitespace
    character removed
    """
    return s.decode('utf-8').strip()


def color_diff(diff):
    """Generator function returns lazy sequence of coloured diff lines"""
    for line in diff:
        if line.startswith('---') or line.startswith('+++'):
            yield str(crayons.black(line, bold=True))
        elif line.startswith('+'):
            yield str(crayons.green(line))
        elif line.startswith('-'):
            yield str(crayons.red(line))
        elif line.startswith('@@'):
            yield str(crayons.cyan(line))
        else:
            yield line


def get_tag(path: str, default=None) -> Optional[str]:
    """
    Returns latest git tag on current branch, defaulting to None if tags cannot
    be found
    """
    # Try and describe the current git repo
    cmd = ['git', 'describe', '--abbrev=0', '--tags']
    try:
        # Capture stdout, discard stderr
        result = run(cmd, stdout=PIPE, stderr=DEVNULL, cwd=path, check=True)
    except CalledProcessError:
        # Return default value if exit code is non zero
        return default
    else:
        return sanitize(result.stdout)


def create_tag(path: str, tag, message):
    """
    Creates a new annotated git tag with tagging message
    """
    cmd = ['git', 'tag', '-a', tag, '-m', message.format(tag)]
    result = run(cmd, cwd=path)
    return result


def find_and_replace(target, old, new, preview=False):
    """
    Finds and replaces content inside a file, returns a diff of changes if
    optional preview flag is passed
    """
    # Create temp file
    fh, abs_path = mkstemp()
    with fdopen(fh, 'r+') as new_file:
        old_lines = target.readlines()
        for line in old_lines:
            new_file.write(line.replace(old, new))
        if preview:
            new_file.seek(0)
            diff = ''.join(unified_diff(
                old_lines,
                new_file.readlines(),
                fromfile=os.path.join('a', target.name),
                tofile=os.path.join('b', target.name)
            ))
    if not preview:
        # Replace file with temp file
        copy(abs_path, target.name)
    else:
        # Remove the temporary file
        remove(abs_path)
        return diff


def strip_prefix(tag) -> Tuple[Optional[str], str]:
    if tag.startswith(tuple(string.ascii_letters)):
        return (tag[PREFIX], tag[REST])
    return (None, tag)


def runchecks(cwd):
    # Immediately Bail if git isn't found
    if not which('git'):
        sys.exit('Error: git executable not found on current $PATH, aborting')

    # Checks if cwd is a git repository
    if not is_git_repo(cwd):
        print('Error: {} not a git repository'.format(cwd), file=sys.stderr)
        if confirm('\nInitialize git repositroy?'):
            run(['git', 'init'])
        sys.exit(1)


def main():

    # Parse command line arguments
    args = parse_args(sys.argv[1:])

    # Get directory from where script was called
    cwd = os.getcwd()

    # Validate current environment before proceeding
    runchecks(cwd)

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
        args.bump = choice(question, choices, allow_prefix=True)

    current_tag = Semver(tag)
    next_tag = str(current_tag.bump(args.bump))

    # Print version diff preview
    if args.preview:
        old, new = ('{}{}\n'.format(prefix or '', v) for v in (tag, next_tag))
        diff = ''.join(color_diff(ndiff([old], [new])))
        print(crayons.magenta('\nVersion Diff:'), diff, sep='\n')

    # If previous tag had a prefix, rejoin the prefix after bumping
    if prefix is not None:
        next_tag = prefix + next_tag

    if args.files:
        # Strip prefix from files
        _, new_tag = strip_prefix(next_tag)
        # Replace tag in each file
        diffs = [
            find_and_replace(f, tag, new_tag, args.preview) for f in args.files
        ]
        # Get names of all the files
        file_names = [f.name for f in args.files]
        # Print diffs (if any exist)
        if any(diffs):
            for fname, diff in zip(file_names, diffs):
                print('\n'.join(color_diff(diff.split('\n'))))

        # Log & commit changes if not in preview mode
        if not args.preview:
            fnames = ', '.join(file_names)
            print(crayons.red("\n  modified: {} ").format(fnames))
            if confirm('\nCommit changes?'):
                run(['git', 'add'] + file_names)
                run(['git', 'commit', '-m', '"bump version number"'])

    # Exit without creating tag if --no-tag positional argument is passed
    if args.no_tag or args.preview:
        sys.exit()

    # Create the tag
    result = create_tag(cwd, next_tag, args.message)
    if result.returncode == 0:
        success_msg = '\n  Created new tag: {}'.format(next_tag)
        print(crayons.green(success_msg))
