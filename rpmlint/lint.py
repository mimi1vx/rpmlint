import importlib
import sys
from tempfile import gettempdir
from concurrent.futures import ThreadPoolExecutor, wait

from rpmlint.config import Config
from rpmlint.filter import Filter
from rpmlint.helpers import print_warning


class Lint(object):
    """
    Generic object handling the basic rpmlint operations
    """

    def __init__(self, options):
        # initialize configuration
        self.checks = {}
        self.options = options
        if options['config']:
            self.config = Config(options['config'])
        else:
            self.config = Config()
        if options['verbose']:
            self.config.info = options['verbose']
        if not self.config.configuration['ExtractDir']:
            self.config.configuration['ExtractDir'] = gettempdir()
        # initialize output buffer
        self.output = Filter(self.config)
        self.load_checks()

    def run(self):
        # if we just want to print config, do so and leave
        if self.options['print_config']:
            self.print_config()
            return 0
        # just explain the error and abort too
        if self.options['explain']:
            self.print_explanation(self.options['explain'])
            return 0
        # if no exclusive option is passed then just loop over all the
        # arguments that are supposed to be either rpm or spec files
        return self.validate_files(self.options['rpmfile'])

    def info_error(self, errors):
        """
        Print details for specified error/s.
        """
        self.output.info = True
        for e in sorted(errors):
            print(f'{e}:')
            print(self.output.get_description(e))

    def validate_files(self, files):
        """
        Run all the check for passed file list
        """
        if not files:
            print('There are no files to process nor additional arguments.', file=sys.stderr)
            print('Nothing to do, aborting.', file=sys.stderr)
            return 2
        with ThreadPoolExecutor as executor:
            futures = [executor.submit(self.validate_file, pkg) for pkg in files]
        wait(futures)
        return 0

    def validate_file(self, pkg):
        try:
            if pkg.endswith('.rpm') or \
               pkg.endswith('.spm'):
                with Pkg.Pkg(fname, extract_dir) as pkg:
                    runChecks(pkg)
                packages_checked += 1
            elif fname.endswith('.spec'):
                with Pkg.FakePkg(fname) as pkg:
                    runSpecChecks(pkg, fname)
                specfiles_checked += 1
        except Exception as e:
            print_warning(f'(none): E: while reading {pkg}: {e}')

    def print_config(self):
        """
        Just output the current configuration
        """
        self.config.print_config()

    def print_explanation(self, message):
        """
        Print out detailed explanation for the specified message
        """
        explanation = self.output.get_description(message)
        if explanation:
            print(explanation)
        else:
            print(f'Unknown message {message}, or no known description')

    def load_checks(self):
        """
        Load all checks based on the config, skipping those already loaded
        SingletonTM
        """

        for check in self.config.configuration['Checks']:
            if check in self.checks:
                continue
            self.checks[check] = self.load_check(check)

    def load_check(self, name):
        """Load a (check) module by its name, unless it is already loaded."""
        module = importlib.import_module(f'.{name}', package='rpmlint.checks')
        klass = getattr(module, name)
        obj = klass(self.config, self.output)
        return obj
