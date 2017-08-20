import os
import sys
from argparse import Namespace
from io import TextIOWrapper
from re import match
from subprocess import CalledProcessError, CompletedProcess
from unittest.mock import Mock, call, mock_open, patch

import pytest

from taggy.cli import (
    color_diff,
    create_tag,
    find_and_replace,
    get_tag,
    is_git_repo,
    main,
    parse_args,
    runchecks,
    sanitize,
    strip_prefix
)


class TestArgumentParsing:

    def test_calls_system_exit_on_invalid_args(self, capsys):
        with pytest.raises(SystemExit):
            parse_args(['--no-tag'])
        out, err = capsys.readouterr()
        msg = err.strip().split("\n").pop()
        assert match(".* --files are required when --no-tag is set", msg)

    def test_provides_default_message(self):
        args = parse_args([])
        assert args.message == 'version {}'

    def test_parses_files(self):
        args = parse_args(['--files', 'setup.py', 'README.rst'])
        assert all(isinstance(x, TextIOWrapper) for x in args.files)
        assert len(args.files) == 2

    def test_parses_message(self):
        args = parse_args(['--message', 'new version {}'])
        assert args.message == 'new version {}'

    @patch('taggy.cli.crayons')
    def test_no_color_flag_disables_crayons(self, mock_crayons):
        parse_args(['--no-color'])
        assert mock_crayons.disable.called_once

    @patch('taggy.cli.__version__')
    def test_version_flag(self, mock_version, capsys):
        mock_version.__str__.return_value = '1.2.3'
        with pytest.raises(SystemExit):
            parse_args(['--version'])
        out, _ = capsys.readouterr()
        assert out.strip() == "Current version: 1.2.3"


class TestUtils:

    @patch('taggy.cli.run', **{'return_value.returncode': 0})
    def test_is_git_repo(self, mock_run):
        out = is_git_repo('/sample/path')
        assert out

    def test_sanitize(self):
        b = bytes(' hello world ', 'utf-8')
        assert sanitize(b) == 'hello world'

    @patch('taggy.cli.crayons')
    def test_color_diff(self, mock_crayons):
        diff = (
            "--- a/folder/docs.conf",
            "+++ b/folder/docs.conf",
            "@@ -1 +1 @@",
            "-version = '2.0.1'",
            "+version = '2.0.2'",
        )
        # Consume entire generator
        tuple(color_diff(diff))

        # Assert crayon colours called for each line
        assert mock_crayons.black.called
        assert mock_crayons.cyan.called
        assert mock_crayons.red.called
        assert mock_crayons.green.called

        assert list(color_diff(['plain line'])) == ['plain line']

    @patch('taggy.cli.run', **{'return_value.stdout': bytes('0.1.0', 'utf-8')})
    def test_get_tag(self, mock_run):
        assert get_tag('/fake/path') == '0.1.0'

    @patch('taggy.cli.run', side_effect=CalledProcessError(1, ''))
    def test_get_tag_on_error(self, mock_run):
        """
        Tests function returns a default value if subprocess returns a non zero
        exit code
        """
        assert get_tag('/fake/path', '0.1.0') == '0.1.0'

    @patch('taggy.cli.run')
    def test_create_tag(self, mock_run):
        mock_run.return_value = CompletedProcess('', returncode=0)
        create_tag('/fake/path', '2.0.0', 'new tag: {}')
        args, kwargs = mock_run.call_args
        assert args == (['git', 'tag', '-a', '2.0.0', '-m', 'new tag: 2.0.0'],)
        assert kwargs == {'cwd': '/fake/path'}

    def test_strip_prefix(self):
        assert strip_prefix('v1.0.1') == ('v', '1.0.1')
        assert strip_prefix('1.0.1') == (None, '1.0.1')


class TestRunChecks:

    @patch('taggy.cli.which', return_value=False)
    def test_aborts_if_git_executable_not_found(self, mock_which):
        with pytest.raises(SystemExit) as error:
            runchecks('/fake/path')
        message = 'Error: git executable not found on current \$PATH, aborting'
        error.match(message)

    @patch('taggy.cli.is_git_repo', return_value=False)
    def aborts_if_not_git_repository(self, mock_is_git_repo):
        with pytest.raises(SystemExit):
            with patch('taggy.cli.which', return_value=True):
                runchecks('/fake/path')
                assert mock_is_git_repo.called

    @patch('taggy.cli.confirm', return_value=False)
    @patch('taggy.cli.is_git_repo', return_value=False)
    def test_prompts_git_repo_creation(self, _, mock_confirm, capsys):
        with pytest.raises(SystemExit):
            with patch('taggy.cli.which', return_value=True):
                runchecks('/fake/path')
                assert mock_confirm.called
        _, err = capsys.readouterr()
        assert match('Error: /fake/path not a git repository', err)

    @patch('taggy.cli.is_git_repo', return_value=False)
    @patch('taggy.cli.confirm', return_value=True)
    @patch('taggy.cli.run', return_value=False)
    def test_creates_git_repo_on_confirm(self, mock_run, _, __):
        with pytest.raises(SystemExit):
            with patch('taggy.cli.which', return_value=True):
                runchecks('/fake/path')
                assert mock_run.called_once_with(['git', 'init'])

    @patch('taggy.cli.is_git_repo', return_value=True)
    def test_runcheck_returns_none_if_valid(self, mock_is_git_repo):
        with patch('taggy.cli.which', return_value=True):
            assert runchecks('/fake/path') is None


class TestFindAndReplace:

    @patch('taggy.cli.remove')
    @patch('taggy.cli.mkstemp', return_value=(3, '/tmp/example'))
    def test_with_preview(self, mock_mkstemp, mock_remove):
        m = mock_open()
        with patch('builtins.open', mock_open(read_data='foo')) as f:
            with open('sample/path') as fi:
                fi.name = "sample/path"
                with patch('taggy.cli.fdopen', m, create=True):
                    diff = find_and_replace(
                        fi, 'foo', 'bar', preview=True
                    )
                    f.assert_called_once_with('sample/path')
                    m.assert_called_once_with(3, 'r+')
                    mock_remove.assert_called_once_with('/tmp/example')
                    new_file_handle = m()
                    new_file_handle.write.assert_called_once_with('bar')
                    new_file_handle.seek.assert_called_once_with(0)
                    assert diff

    @patch('taggy.cli.copy')
    @patch('taggy.cli.mkstemp', return_value=(3, '/tmp/example'))
    def test_replaces_content(self, mock_mkstemp, mock_copy):
        m = mock_open()
        with patch('builtins.open', mock_open(read_data='foo')) as f:
            with open('sample/path') as fi:
                fi.name = "sample/path"
                with patch('taggy.cli.fdopen', m, create=True):
                    find_and_replace(fi, 'foo', 'bar')
                    f.assert_called_once_with('sample/path')
                    m.assert_called_once_with(3, 'r+')
                    mock_copy.assert_called_once_with(
                        '/tmp/example', 'sample/path'
                    )
                    new_file_handle = m()
                    new_file_handle.write.assert_called_once_with('bar')


class TestInitalTagCreation:
    """
    Tests user is prompted to create an intial tag if no pre-exsiting git tag
    is found
    """

    @patch('taggy.cli.runchecks')
    @patch('taggy.cli.get_tag', return_value=None)
    @patch('taggy.cli.confirm', return_value=False)
    def test_prompts_for_tag_creation(self, _, __, ___):
        with pytest.raises(SystemExit):
            with patch.object(sys, 'argv', ['taggy']):
                main()

    @patch('taggy.cli.runchecks')
    @patch('taggy.cli.get_tag', return_value=None)
    @patch('taggy.cli.confirm', return_value=True)
    @patch('taggy.cli.create_tag')
    def test_creates_tag_on_confirmation(self, mock_create, _, __, ___):
        with pytest.raises(SystemExit):
            with patch.object(sys, 'argv', ['taggy']):
                with patch('os.getcwd', return_value='/home/user/proj'):
                    main()
                    assert mock_create.called_once_with(
                        '/home/user/proj', '0.1.0', 'version {}'
                    )


class TestHandlesArgs:

    @patch('taggy.cli.runchecks')
    @patch('taggy.cli.get_tag', return_value='2.1.0')
    @patch('taggy.cli.choice', return_value='patch')
    def test_prompts_for_bump_arg(self, mock_choice, __, ___):
        with patch.object(sys, 'argv', ['taggy']):
            main()
            assert mock_choice.called_once_with(
                'Choose: [M]ajor/[m]inor/[p]atch: ',
                ('Major', 'minor', 'patch'),
                allow_prefix=True
            )

    @patch('taggy.cli.runchecks')
    @patch('taggy.cli.get_tag', return_value='2.1.0')
    def test_prints_preview(self, _, __, capsys):
        with pytest.raises(SystemExit):
            with patch.object(sys, 'argv', ['taggy', 'patch', '--preview']):
                main()
        out, _ = capsys.readouterr()
        assert out.strip() == '\n'.join((
            "Version Diff:",
            "- 2.1.0",
            "?     ^",
            "+ 2.1.1",
            "?     ^",
        ))


class TestWithFilePositionalArgs:

    @classmethod
    def setup_class(cls):
        # Create some mock files
        f1 = Mock(spec=TextIOWrapper)
        f1.readlines.return_value = ['2.1.0\n']
        f1.name = "foo.py"
        f2 = Mock(spec=TextIOWrapper)
        f2.readlines.return_value = ['2.1.0\n']
        f2.name = "bar.py"
        cls.files = [f1, f2]

    @patch('taggy.cli.runchecks')
    @patch('taggy.cli.get_tag', return_value='v2.1.0')
    @patch('taggy.cli.create_tag')
    @patch('taggy.cli.parse_args')
    def test_shows_file_diffs_on_preview(self, mock_args, _, __, ___, capsys):
        files = self.files
        ns = Namespace(bump='patch', files=files, preview=True, no_tag=True)
        mock_args.return_value = ns
        with pytest.raises(SystemExit):
            main()
        out, err = capsys.readouterr()
        assert out == "\n".join((
            "\nVersion Diff:",
            "- v2.1.0",
            "?      ^",
            "+ v2.1.1",
            "?      ^",
            "\n--- a/foo.py",
            "+++ b/foo.py",
            "@@ -1 +1 @@",
            "-2.1.0",
            "+2.1.1",
            "\n--- a/bar.py",
            "+++ b/bar.py",
            "@@ -1 +1 @@",
            "-2.1.0",
            "+2.1.1\n\n"
        ))

    @patch('taggy.cli.runchecks')
    @patch('taggy.cli.get_tag', return_value='v2.1.0')
    @patch('taggy.cli.copy')
    @patch('taggy.cli.parse_args')
    def test_commits_changes(self, mock_args, _, __,  ___, capsys):
        files = self.files
        ns = Namespace(bump='patch', files=files, preview=False, no_tag=True)
        mock_args.return_value = ns
        with patch('taggy.cli.run') as mock_run:
            with pytest.raises(SystemExit):
                with patch('taggy.cli.confirm', return_value=True):
                    main()
            assert mock_run.call_args_list == [
                (call(['git', 'add', 'foo.py', 'bar.py'])),
                (call(['git', 'commit', '-m', '"bump version number"']))
            ]

    @patch('taggy.cli.runchecks')
    @patch('taggy.cli.get_tag', return_value='v2.1.0')
    @patch('taggy.cli.run')
    @patch('taggy.cli.parse_args')
    def test_skip_commit_on_prompt(self, mock_args, mock_run, _, __, capsys):
        files = self.files
        ns = Namespace(bump='patch', files=files, preview=False, no_tag=True)
        mock_args.return_value = ns
        with pytest.raises(SystemExit):
            with patch('taggy.cli.confirm', return_value=False):
                with patch('taggy.cli.copy'):
                    main()
        with patch('taggy.cli.run') as mock_run:
            assert not mock_run.called


class TestTagCreation:

    @patch('taggy.cli.runchecks')
    @patch('taggy.cli.get_tag', return_value='v2.1.0')
    @patch('taggy.cli.create_tag')
    def test_handles_prefix(self, mock_create_tag, _, __):
        with patch.object(sys, 'argv', ['taggy', 'patch']):
            with patch.object(os, 'getcwd', return_value='/sample/path'):
                main()
                assert mock_create_tag.called_once_with(
                    ['/sample/path', 'v2.1.1', 'version {}']
                )

    @patch('taggy.cli.runchecks')
    @patch('taggy.cli.get_tag', return_value='2.1.0')
    @patch('taggy.cli.create_tag', **{'return_value.returncode': 0})
    def test_success_message(self, mock_create_tag, _, __, capsys):
        with patch.object(sys, 'argv', ['taggy', 'patch']):
            with patch.object(os, 'getcwd', return_value='/sample/path'):
                main()
                assert mock_create_tag.called_once_with(
                    ['/sample/path', 'v2.1.1', 'version {}']
                )
        out, err = capsys.readouterr()
        assert out.strip() == 'Created new tag: 2.1.1'
