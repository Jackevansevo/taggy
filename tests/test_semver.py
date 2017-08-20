from taggy.semver import Semver, InvalidSemanticVersion
import pytest


@pytest.mark.parametrize("data, part, expected", [
    ('3.4.5', 'major', '4.0.0'),
    ('3.4.5', 'minor', '3.5.0'),
    ('3.4.5', 'patch', '3.4.6'),
    ('3.4.5-rc1+build4', 'patch', '3.4.6'),
])
def test_semver(data, part, expected):
    version = Semver(data)
    assert str(version.bump(part)) == expected


def test_repr():
    version = Semver("3.4.5")
    assert repr(version) == "<Semantic Version (major=3 minor=4 patch=5)>"


def test_should_parse_zero_prerelease():
    result = Semver("1.2.3-rc.0+build.0")

    assert vars(result) == {
        'major': 1,
        'minor': 2,
        'patch': 3,
        'prerelease': 'rc.0',
        'build': 'build.0',
    }

    result = Semver("1.2.3-rc.0.0+build.0")

    assert vars(result) == {
        'major': 1,
        'minor': 2,
        'patch': 3,
        'prerelease': 'rc.0.0',
        'build': 'build.0',
    }


def test_should_parse_version():
    result = Semver("1.2.3-alpha.1.2+build.11.e0f985a")
    assert vars(result) == {
        'major': 1,
        'minor': 2,
        'patch': 3,
        'prerelease': 'alpha.1.2',
        'build': 'build.11.e0f985a',
    }

    result = Semver("1.2.3-alpha-1+build.11.e0f985a")
    assert vars(result) == {
        'major': 1,
        'minor': 2,
        'patch': 3,
        'prerelease': 'alpha-1',
        'build': 'build.11.e0f985a',
    }


def check_validity(tag):
    with pytest.raises(InvalidSemanticVersion) as error:
        Semver(tag)
    assert str(error.value) == "{} is an invalid Semantic version".format(tag)


def test_raises_exception_on_invalid_prerelease():
    check_validity('1.0.1-$')


def test_raises_exception_on_missing_part():
    check_validity('1.0')
