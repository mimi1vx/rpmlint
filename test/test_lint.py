from rpmlint.lint import Lint

from Testing import TEST_CONFIG

option_presets = {
    'config': TEST_CONFIG,
    'verbose': False,
    'print_config': False,
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
    linter = Lint(option_presets)
    assert list(linter.checks.keys()) == basic_tests


def test_configoutput(capsys):
    additional_options = {
        'print_config': True,
    }
    options = {**option_presets, **additional_options}
    linter = Lint(options)
    linter.run()
    out, err = capsys.readouterr()
    assert out
    assert "'Vendor': 'Fedora Project'" in out
    assert not err
