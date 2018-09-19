#!/usr/bin/python3
#############################################################################
# File          : rpmlint
# Package       : rpmlint
# Author        : Frederic Lepied
# Created on    : Mon Sep 27 19:20:18 1999
# Purpose       : main entry point: process options, load the checks and run
#                 the checks.
#############################################################################

import contextlib
import getopt
import locale
import os
import stat
import sys

# Do not import anything that initializes its global variables from
# Config at load time here (or anything that imports such a thing),
# that results in those variables initialized before config files are
# loaded which is too early - settings from config files won't take
# place for those variables.

from rpmlint import pkg as Pkg
from rpmlint.checks.AbstractCheck import AbstractCheck
from rpmlint.config import Config
from rpmlint.filter import Filter
from rpmlint.helpers import print_warning



#############################################################################
# main program
#############################################################################
def main():

    # we'll try to sort with locale settings, but we don't fail if not possible
    with contextlib.suppress(locale.Error):
        locale.setlocale(locale.LC_COLLATE, '')

    output = Filter(cfg)

    # Load all checks
    for c in cfg.configuration['Checks']:
        loadCheck(c, cfg, output)

    packages_checked = 0
    specfiles_checked = 0

    try:
        # Loop over all file names given in arguments
        dirs = []
        for arg in args:
            pkgs = []
            isfile = False
            try:
                if arg == '-':
                    arg = '(standard input)'
                    # Short-circuit stdin spec file check
                    stdin = sys.stdin.readlines()
                    if not stdin:
                        continue
                    with Pkg.FakePkg(arg) as pkg:
                        runSpecChecks(pkg, None, spec_lines=stdin)
                    specfiles_checked += 1
                    continue

                try:
                    st = os.stat(arg)
                    isfile = True
                    if stat.S_ISREG(st[stat.ST_MODE]):
                        if arg.endswith('.spec'):
                            # Short-circuit spec file checks
                            with Pkg.FakePkg(arg) as pkg:
                                runSpecChecks(pkg, arg)
                            specfiles_checked += 1
                        elif '/' in arg or arg.endswith('.rpm') or \
                                arg.endswith('.spm'):
                            pkgs.append(Pkg.Pkg(arg, extract_dir))
                        else:
                            raise OSError

                    elif stat.S_ISDIR(st[stat.ST_MODE]):
                        dirs.append(arg)
                        continue
                    else:
                        raise OSError
                except OSError:
                    ipkgs = Pkg.getInstalledPkgs(arg)
                    if not ipkgs:
                        print_warning(
                            '(none): E: no installed packages by name %s' % arg)
                    else:
                        ipkgs.sort(key=lambda x: locale.strxfrm(
                            x.header.sprintf('%{NAME}.%{ARCH}')))
                        pkgs.extend(ipkgs)
            except KeyboardInterrupt:
                if isfile:
                    arg = os.path.abspath(arg)
                print_warning(
                    '(none): E: interrupted, exiting while reading %s' % arg)
                sys.exit(2)
            except Exception as e:
                if isfile:
                    arg = os.path.abspath(arg)
                print_warning('(none): E: error while reading %s: %s' % (arg, e))
                pkgs = []
                continue

            for pkg in pkgs:
                with pkg:
                    runChecks(pkg)
                packages_checked += 1

        for dname in dirs:
            try:
                for path, _, files in os.walk(dname):
                    for fname in files:
                        fname = os.path.abspath(os.path.join(path, fname))
                        try:
                            if fname.endswith('.rpm') or \
                               fname.endswith('.spm'):
                                with Pkg.Pkg(fname, extract_dir) as pkg:
                                    runChecks(pkg)
                                packages_checked += 1

                            elif fname.endswith('.spec'):
                                with Pkg.FakePkg(fname) as pkg:
                                    runSpecChecks(pkg, fname)
                                specfiles_checked += 1

                        except KeyboardInterrupt:
                            print_warning(
                                '(none): E: interrupted while reading %s' %
                                fname)
                            sys.exit(2)
                        except Exception as e:
                            print_warning(
                                '(none): E: while reading %s: %s' % (fname, e))
                            continue
            except Exception as e:
                print_warning(
                    '(none): E: error while reading dir %s: %s' % (dname, e))
                continue

        print(output.print_results(output.results))

        if output.badness_threshold > 0 and output.score > output.badness_threshold:
            print_warning('(none): E: badness %d exceeds threshold %d, aborting.' %
                          (output.score, output.badness_threshold))
            sys.exit(66)

    finally:
        print('%d packages and %d specfiles checked; %d errors, %d warnings.'
              % (packages_checked, specfiles_checked,
                 output.printed_messages['E'], output.printed_messages['W']))

    if output.printed_messages['E'] > 0:
        sys.exit(64)
    sys.exit(0)


def runChecks(pkg):
    for name in cfg.configuration['Checks']:
        check = AbstractCheck.known_checks.get(name)
        if check:
            check.check(pkg)
        else:
            print_warning('(none): W: unknown check %s, skipping' % name)


def runSpecChecks(pkg, fname, spec_lines=None):
    for name in cfg.configuration['Checks']:
        check = AbstractCheck.known_checks.get(name)
        if check:
            check.check_spec(pkg, fname, spec_lines)
        else:
            print_warning('(none): W: unknown check %s, skipping' % name)
