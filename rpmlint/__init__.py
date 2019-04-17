import argparse
import os
import sys

from rpmlint.lint import Lint
from rpmlint.rpmdiff import Rpmdiff
from rpmlint.version import __version__


__copyright__ = """
    Copyright (C) 2006 Mandriva
    Copyright (C) 2009 Red Hat, Inc.
    Copyright (C) 2009 Ville Skyttä
    Copyright (C) 2017 SUSE LINUX GmbH
    This program is free software; you can redistribute it and/or
    modify it under the terms of the GNU General Public License
    as published by the Free Software Foundation; either version 2
    of the License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, write to the Free Software
    Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
"""


def process_diff_args(argv):
    """
    Process the passed arguments and return the result
    :param argv: passed arguments
    """

    parser = argparse.ArgumentParser(prog='rpmdiff',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                     description='Shows basic differences between two rpm packages')
    parser.add_argument('old_package', metavar='RPM_ORIG', type=str, help='the old package')
    parser.add_argument('new_package', metavar='RPM_NEW', type=str, help='the new package')
    parser.add_argument('-v', '--version', action='version', version=__version__, help='show package version and exit')
    parser.add_argument('-i', '--ignore', nargs='*', default='', choices=['S', 'M', '5', 'D', 'N', 'L', 'V', 'U', 'G', 'F', 'T'],
                        help="""file property to ignore when calculating differences.
                                Valid values are: S (size), M (mode), 5 (checksum), D (device),
                                N (inode), L (number of links), V (vflags), U (user), G (group),
                                F (digest), T (time)""")

    # print help if there is no argument or less than the 2 mandatory ones
    if len(argv) < 2:
        parser.print_help()
        sys.exit(0)

    options = parser.parse_args(args=argv)

    # convert options to dict
    options_dict = vars(options)
    return options_dict


def process_lint_args(argv):
    """
    Process the passed arguments and return the result
    :param argv: passed arguments
    """

    parser = argparse.ArgumentParser(prog='rpmlint',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                     description='Check for common problems in rpm packages')
    parser.add_argument('rpmfile', nargs='*', default='', help='files to be validated by rpmlint')
    parser.add_argument('-v', '--version', action='version', version=__version__, help='show package version and exit')
    parser.add_argument('-c', '--config', default='', help='load up additional configuration data from specified path')
    parser.add_argument('-e', '--explain', nargs='*', default='', help='provide detailed explanation for one specific message id')
    parser.add_argument('-r', '--rpmlintrc', default='', help='load up specified rpmlintrc file')
    parser.add_argument('-V', '--verbose', action='store_true', help='provide detailed explanations where available')
    parser.add_argument('-p', '--print-config', action='store_true', help='print the settings that are in effect when using the rpmlint')

    # print help if there is no argument
    if len(argv) < 1:
        parser.print_help()
        sys.exit(0)

    options = parser.parse_args(args=argv)

    # make sure config exist
    if options.config:
        if not os.path.exists(options.config):
            print(f'User specified configuration \'{options.config}\' does not exist')
            exit(2)
    # make sure rpmlintrc exists
    if options.rpmlintc:
        if not os.path.exists(options.rpmlintrc):
            print(f'User specified rpmlintrc \'{options.rpmlintrc}\' does not exist')
            exit(2)
    # validate all the rpmlfile options to be either file or folder
    for item in options.rpmfile:
        if not os.path.exists(item):
            print(f'The file or directory \'{item}\' does not exist')
            exit(2)

    # convert options to dict
    options_dict = vars(options)
    return options_dict


def lint():
    """
    Main wrapper for lint command processing
    """
    options = process_lint_args(sys.argv[1:])
    lint = Lint(options)
    sys.exit(lint.run())


def diff():
    """
    Main wrapper for diff command processing
    """
    options = process_diff_args(sys.argv[1:])
    d = Rpmdiff(options['old_package'], options['new_package'], ignore=options['ignore'])
    textdiff = d.textdiff()
    if textdiff:
        print(textdiff)
    sys.exit(int(d.differs()))
