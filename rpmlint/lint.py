import importlib
from tempfile import gettempdir

from rpmlint.config import Config
from rpmlint.filter import Filter


class Lint(object):
    """
    Generic object handling the basic rpmlint operations
    """

    checks = {}

    def __init__(self, options):
        # initialize configuration
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

    def info_error(self, errors):
        """
        Print details for specified error/s.
        """
        self.output.info = True
        for e in sorted(errors):
            print(f'{e}:')
            print(self.output.get_description(e))

    def print_config(self):
        self.config.print_config()

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
        module = importlib.import_module('.{}'.format(name), package='rpmlint.checks')
        klass = getattr(module, name)
        obj = klass(self.config, self.output)
        return obj
