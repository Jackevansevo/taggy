import re
from itertools import chain, islice, repeat

PRERELEASE_REGEX = re.compile("[0-9A-Za-z-]")

SEMVER_NUMS = ('major', 'minor', 'patch')


def pad(iterable, size, padding=None):
    return islice(chain(iterable, repeat(padding)), size)


class InvalidSemanticVersion(Exception):

    def __init__(self, version):
        self.version = version

    def __str__(self):
        return '{} is an invalid Semantic version'.format(self.version)


class Semver:

    def __init__(self, version):

        # x.y.z-prerelease+build
        init, self.build = pad(version.rsplit('+'), 2)

        head, self.prerelease = pad(init.split('-', 1), 2)

        version_nums = pad(map(int, head.split('.')), 3)

        self.major, self.minor, self.patch = version_nums

        if self.prerelease is not None:
            if not PRERELEASE_REGEX.match(self.prerelease):
                raise InvalidSemanticVersion(version)

        if any(part is None for part in (self.major, self.minor, self.patch)):
            raise InvalidSemanticVersion(version)

    @property
    def components(self):
        return dict(zip(SEMVER_NUMS, (self.major, self.minor, self.patch)))

    @property
    def valstrings(self):
        return map(str, (self.major, self.minor, self.patch))

    def bump(self, part):
        part = part.lower()
        for key, value in self.components.items():
            if key == part:
                setattr(self, key, value + 1)
            elif SEMVER_NUMS.index(key) > SEMVER_NUMS.index(part):
                setattr(self, key, 0)
        return self

    def __repr__(self):
        repr_string = "<Semantic Version (major={} minor={} patch={})>"
        return repr_string.format(self.major, self.minor, self.patch)

    def __str__(self):
        return '.'.join(self.valstrings)
