from collections import ChainMap
import sys

PREFIX = slice(0, 1)


class WriteOnceDict(dict):
    def __setitem__(self, key, value):
        if key in self:
            raise KeyError('{} has already been set'.format(key))
        super(WriteOnceDict, self).__setitem__(key, value)


def build_choices(choices, allow_prefix=False):
    options = WriteOnceDict()
    for choice in choices:
        if allow_prefix:
            options[choice[0]] = choice
        options[choice] = choice
    return options


def _prompt_choice(question, options, lower):
    selected = prompt(question)
    if selected in options:
        return options[selected]
    elif lower and selected.lower() in options:
        return options[selected.lower()]
    else:
        return _prompt_choice(question, options, lower)


def choice(question, choices, allow_prefix=False, lower=True):
    options = build_choices(choices, allow_prefix)
    if lower:
        lowered_options = {k.lower(): v for k, v in options.items()}
        options = ChainMap(options, lowered_options)
    return _prompt_choice(question, options, lower)


def prompt(question, lower=False):
    try:
        answer = input(question)
    except (KeyboardInterrupt, EOFError) as error:
        sys.exit("\nInterrupted, quitting")
    else:
        return answer.lower() if lower else answer


def confirm(question):
    text = ' '.join([question, '[Y/n]: '])
    return choice(text, ['yes', 'no'], allow_prefix=True) == 'yes'
