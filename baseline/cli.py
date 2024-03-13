"""
Entry point for manual invocation.
"""

import logging
import argparse

from . import __version__, BaselineBuilder


def main():

    help_menu = [
        f'Baseline Builder v{__version__}',
        'Usage:',
        '- Build a fresh pkg:',
        '>>> python3 baseline.py --build ripeda.plist',
        '',
        '- Validate an existing pkg:',
        '>>> python3 baseline.py --validate ripeda.mobileconfig RIPEDA.pkg',
        '   (pkg and mobileconfig positions can be swapped)',
        '>>> python3 baseline.py --validate RIPEDA.pkg',
        '   (will resolve to embedded config)',
    ]

    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        handlers=[logging.StreamHandler()]
    )

    parser = argparse.ArgumentParser(description='Build a baseline from a configuration file or validate existing pkg.', add_help=False)
    parser.add_argument('-b', '--build',    metavar='CONFIGURATION')
    parser.add_argument('-v', '--validate', metavar=('CONFIGURATION', 'PKG'), nargs='+')
    parser.add_argument('-h', '--help',     action="store_true",)

    args = parser.parse_args()

    if args.build is not None:
        baseline_obj = BaselineBuilder(configuration_file=args.build)

        baseline_obj.build()
        baseline_obj.validate_pkg()

    if args.validate is not None:
        pkg_arg    = args.validate[0]
        config_arg = None

        if len(args.validate) == 2:
            pkg_arg    = args.validate[0] if args.validate[0].endswith(".pkg") else args.validate[1]
            config_arg = args.validate[0] if args.validate[0].endswith(".mobileconfig") else args.validate[1]

        if config_arg is None:
            config_arg = ".plist"

        baseline_obj = BaselineBuilder(configuration_file=config_arg)
        baseline_obj.validate_pkg(pkg=pkg_arg)

    if args.help is True:
        for line in help_menu:
            logging.info(line)