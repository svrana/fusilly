#!/usr/bin/env python

import argparse
import json # noqa
import logging
import os
import os.path
import sys

# pylint: disable=W0611
from fusilly.targets import Targets
from fusilly.targets import *   # noqa

stream_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
stream_handler.setFormatter(formatter)
root_logger = logging.getLogger('')
root_logger.addHandler(stream_handler)
logger = logging.getLogger(__name__)


class BuildFile(object):
    def __init__(self, project_root, path):
        self.project_root = project_root
        self.path = path
        self.dir = os.path.dirname(path)
        self._source = None

    def source(self):
        if self._source is None:
            with open(self.path, 'r') as f:
                self._source = f.read()
        return self._source


class BuildFiles(object):
    """ A collection of BuildFiles that is able to locate all the BUILD files
    of a project. """
    def __init__(self):
        self.project_root = None
        self.builds = []

    def find_build_files_in(self, directory):
        builds = []
        # TODO: global config file, living at root to control things like this
        third_party_dirs = ['vendor', 'node_modules']
        for root, dirs, files in os.walk(directory, topdown=True):
            # skip over hidden directories...
            # skip over the case where go has brought in deps that contain
            # their own BUILD files.
            dirs[:] = [d for d in dirs if not d[0] == '.' or
                       d in third_party_dirs]
            logger.debug("Checking %s for build files", root)
            if 'BUILD' in files:
                buildFilePath = os.path.join(root, 'BUILD')
                buildFile = BuildFile(self.project_root, buildFilePath)
                logger.debug("Found %s", buildFilePath)
                builds.append(buildFile)
        return builds

    def find_project_root(self):
        # Meh, could insist on PYTHONPATH though that would mean would only
        # work in dev settings, so looking around for repo root.
        dirs = ['.git']

        cwd = os.getcwd()
        while cwd != '/':
            roots = [os.path.join(cwd, d) for d in dirs]
            for root in roots:
                if os.path.exists(root):
                    return os.path.dirname(root)
            cwd = os.path.abspath(os.path.join(cwd, '..'))

        return None

    def find_build_files(self):
        self.project_root = self.find_project_root()
        if self.project_root is None:
            logger.error("Could not find project root. Check directory.")
            sys.exit(1)
        self.builds = self.find_build_files_in(self.project_root)
        return self

    def load(self):
        self.find_build_files()
        if not self.builds:
            logging.error("Could not locate any BUILD files under %s",
                          self.project_root)
            sys.exit(1)

        for buildFile in self.builds:
            logger.debug("Loading BUILD from %s", buildFile.dir)

            # pylint: disable=W0122
            exec(buildFile.source(), globals(), locals())

            # We don't know which targets were just loaded, but we need each
            # one to know which buildFile its associated with.
            # TODO: should be able to pass this in the environment during exec
            # and grab it from there.
            Targets.maybe_set_buildfile(buildFile)


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
                                          help='Project to build')
    for target in Targets.itervalues():
        tp = subparsers.add_parser(
            target.name, help='%s %s' % (cmd, target.name),
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
        add_dep_cmdline_opts(tp, target)

def build_target(buildFiles, programArgs):
    argParser = argparse.ArgumentParser(description='Build project')
    add_target_subparser('build', argParser)

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


def main():
    COMMANDS = {
        'build': build_target,
    }

    argParser = argparse.ArgumentParser(description='Build and bundle')
    argParser.add_argument('command', choices=COMMANDS)
    argParser.add_argument('--logging', choices=['info', 'warn', 'debug'],
                           help='log level', default='info')
    argParser.add_argument('args', nargs=argparse.REMAINDER)
    args = argParser.parse_args()

    root_logger.setLevel(args.logging.upper())

    buildFiles = BuildFiles()
    buildFiles.load()

    if not Targets:
        logger.error("No targets found")
        sys.exit(1)

    COMMANDS[args.command](buildFiles, args)


if __name__ == '__main__':
    main()
