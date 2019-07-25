from pathlib import Path

import pytest
from rpmlint.lint import Lint

from Testing import TEST_CONFIG

options_preset = {
    'config': TEST_CONFIG,
    'verbose': False,
    'print_config': False,
    'explain': False,
    'rpmfile': False,
    'rpmlintrc': False,
}

basic_tests = [
    'DistributionCheck',
    'TagsCheck',
    'BinariesCheck',
    'ConfigCheck',
    'FilesCheck',
    'DocFilesCheck',
    'FHSCheck',
    'SignatureCheck',
    'I18NCheck',
    'MenuCheck',
    'PostCheck',
    'InitScriptCheck',
    'SourceCheck',
    'SpecCheck',
    'NamingPolicyCheck',
    'ZipCheck',
    'PamCheck',
    'RpmFileCheck',
    'MenuXDGCheck',
    'AppDataCheck',
]


def test_cases_loading():
    linter = Lint(options_preset)
    assert list(linter.checks.keys()) == basic_tests


def test_configoutput(capsys):
    additional_options = {
        'print_config': True,
    }
    options = {**options_preset, **additional_options}
    linter = Lint(options)
    linter.run()
    out, err = capsys.readouterr()
    assert out
    assert "'Vendor': 'Fedora Project'" in out
    assert not err


def test_explain_unknown(capsys):
    message = 'bullcrap'
    additional_options = {
        'explain': message,
    }
    options = {**options_preset, **additional_options}
    linter = Lint(options)
    linter.run()
    out, err = capsys.readouterr()
    assert 'Unknown message' in out
    assert not err


def test_explain_known(capsys):
    message = 'infopage-not-compressed'
    additional_options = {
        'explain': message,
    }
    options = {**options_preset, **additional_options}
    linter = Lint(options)
    linter.run()
    out, err = capsys.readouterr()
    assert 'This info page is not compressed' in out
    assert 'Unknown message' not in out
    assert not err


@pytest.mark.parametrize('packages', [Path('test/source/wrongsrc-0-0.src.rpm')])
def test_run_single(capsys, packages):
    additional_options = {
        'rpmfile': [packages],
    }
    options = {**options_preset, **additional_options}
    linter = Lint(options)
    linter.run()
    out, err = capsys.readouterr()
    assert 'E: no-signature' in out
    assert '1 packages and 0 specfiles checked' in out
    assert not err


@pytest.mark.parametrize('packages', [list(Path('test').glob('*/*.rpm'))])
def test_run_full_rpm(capsys, packages):
    number_of_pkgs = len(packages)
    additional_options = {
        'rpmfile': packages,
    }
    options = {**options_preset, **additional_options}
    linter = Lint(options)
    linter.run()
    out, err = capsys.readouterr()
    assert f'{number_of_pkgs} packages and 0 specfiles checked' in out
    # we convert the err as we don't care about errors from missing
    # spellchecking dictionaries -> we have to ignore it
    err_reduced = [a for a in err.split('\n') if not a.startswith('(none): W: unable to load spellchecking dictionary for') and a != '']
    # also we can find out signatures are wrong because of the other distros
    # could've signed it
    err_reduced = [a for a in err_reduced if not a.startswith('Error checking signature of')]
    assert not err_reduced


@pytest.mark.parametrize('packages', [list(Path('test/spec').glob('*.spec'))])
def test_run_full_specs(capsys, packages):
    number_of_pkgs = len(packages)
    additional_options = {
        'rpmfile': packages,
    }
    options = {**options_preset, **additional_options}
    linter = Lint(options)
    linter.run()
    out, err = capsys.readouterr()
    assert f'0 packages and {number_of_pkgs} specfiles checked' in out
    assert not err


def test_run_empty(capsys):
    linter = Lint(options_preset)
    linter.run()
    out, err = capsys.readouterr()
    assert err
    assert '0 packages and 0 specfiles checked; 0 errors, 0 warnings' in out