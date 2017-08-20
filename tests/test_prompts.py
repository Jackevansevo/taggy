from unittest.mock import patch

import pytest
from taggy.prompts import build_choices, choice, confirm, prompt

CHOICES = ('Major', 'minor', 'patch')


@patch('builtins.input', lambda _: 'Homer')
def test_prompt_lowers_input():
    assert prompt('What is your name', lower=True) == 'homer'


@patch('builtins.input')
def test_prompt_quits_on_interrupt(mock_input):
    mock_input.side_effect = KeyboardInterrupt
    with pytest.raises(SystemExit) as error:
        prompt('What is your name')
    error.match('\nInterrupted, quitting')


@patch('builtins.input', lambda _: 'y')
def test_confirm():
    assert confirm('Make git repository?')


@patch('builtins.input', lambda _: 'M')
def test_choice_accepts_prefix():
    answer = choice('Choose: ', choices=CHOICES, allow_prefix=True)
    assert answer == 'Major'


@patch('builtins.input', lambda _: 'MAJOR')
def test_choice_lowers_case():
    answer = choice('Choose: ', choices=CHOICES)
    assert answer == 'Major'


@patch('builtins.input', side_effect=['major', 'MAJOR'])
def test_choice_case_insensitive_by_default(mock_input):
    answer = choice('Choose: ', choices=CHOICES)
    assert answer == 'Major'
    answer = choice('Choose:', choices=CHOICES)
    assert answer == 'Major'


@patch('builtins.input', side_effect=['MAJOR', 'patch'])
def test_choice_with_lower_disabled(mock_input):
    """Tests case sensitivity is respected when lower kwarg is False"""
    answer = choice('Choice:', choices=CHOICES, lower=False)
    assert answer == 'patch'


@patch('builtins.input', side_effect=['mazor', 'major'])
def test_choice_retries_on_failure(mock_input):
    """
    Tests the function will continue to retry until a valid option
    has been entered
    """
    answer = choice('Choose: ', choices=CHOICES)
    assert answer == 'Major'


def test_build_choices_with_prefix():
    assert build_choices(["Major", "minor", "patch"], allow_prefix=True) == {
        'M': 'Major',
        'Major': 'Major',
        'm': 'minor',
        'minor': 'minor',
        'p': 'patch',
        'patch': 'patch'
    }


def test_build_choices_with_duplicate_keys():
    with pytest.raises(KeyError) as error:
        build_choices(['bacon', 'brownies', 'cookies'], allow_prefix=True)
    error.match(r'b has already been set')
