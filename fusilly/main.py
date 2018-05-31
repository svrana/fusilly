#!/usr/bin/env python

import argparse
import logging
import signal
import sys

from fusilly.command import Command
from fusilly.buildfiles import BuildFiles
# pylint: disable=W0611
from fusilly.targets import Targets


stream_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
stream_handler.setFormatter(formatter)
root_logger = logging.getLogger('')
root_logger.addHandler(stream_handler)
logger = logging.getLogger(__name__)


def add_dep_cmdline_opts(parser, target):
    for dep in target.deps:
        dep_target = Targets.get(dep)
        add_dep_cmdline_opts(parser, dep_target)

    for optname, default_value in target.custom_options.iteritems():
        option = '--%s' % optname
        # non-empty help to get the ArgumentDefaultsHelpFormatter to show
        # the defaults
        parser.add_argument(option, type=str, default=default_value, help=' ')


def add_target_subparser(cmd, argParser):
    subparsers = argParser.add_subparsers(dest='subparser_name',
                                          help='Target to run')
    for target in Targets.itervalues():
        tp = subparsers.add_parser(
            target.name, help='%s %s' % (cmd, target.name),
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
        add_dep_cmdline_opts(tp, target)


def run_target(programArgs):
    argParser = argparse.ArgumentParser(description='Run target')
    add_target_subparser('run', argParser)

    argParser.add_argument('args', nargs=argparse.REMAINDER)
    subArgs = argParser.parse_args(programArgs.args)
    target_name = subArgs.subparser_name
    target = Targets.get(target_name)

    if target._check():
        sys.exit(1)

    logger.info("Building %s...", target.name)

    try:
        target._run(subArgs, {})
    finally:
        target._cleanup()


def signal_handler(sig, frame):
    Command.sigterm_handler()
    logger.info('exiting..')
    sys.exit(1)


def main():
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    COMMANDS = {
        'run': run_target,
    }

    argParser = argparse.ArgumentParser(
        description='Interact with targets defined in fusilly BUILD files'
    )
    argParser.add_argument('command', choices=COMMANDS)
    argParser.add_argument('--logging', choices=['info', 'warn', 'debug'],
                           help='log level', default='info')
    argParser.add_argument('args', nargs=argparse.REMAINDER)
    args = argParser.parse_args()

    root_logger.setLevel(args.logging.upper())

    buildFiles = BuildFiles()
    buildFiles.load()

    COMMANDS[args.command](args)


if __name__ == '__main__':
    main()
