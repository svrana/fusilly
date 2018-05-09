#!/usr/bin/env python

import argparse
import collections
import os
import os.path
import logging
import sys

from glob2 import glob

from fusilly.deb import Deb
from fusilly.exceptions import DuplicateTargetError, BuildConfigError
from fusilly.virtualenv import Virtualenv
from fusilly.utils import to_iterable, is_installed


stream_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
stream_handler.setFormatter(formatter)
root_logger = logging.getLogger('')
root_logger.addHandler(stream_handler)
logger = logging.getLogger(__file__)


class Target(object):
    def __init__(self, name, files, exclude_files=None, pip_requirements=None,
                 artifact=None, **kwargs):
        self.name = name
        self.files = to_iterable(files)
        self.exclude_files = to_iterable(exclude_files)
        self.pip_requirements = to_iterable(pip_requirements)
        self.run = kwargs.get('run')
        self.artifact = artifact
        if not isinstance(self.artifact, dict):
            raise BuildConfigError("artifact must be a dictionary")
        if not self.artifact.get('name'):
            raise BuildConfigError("artifact must contain a 'name' key")
        if not self.artifact.get('type'):
            raise BuildConfigError("artifact must contain a 'type' key")
        self.artifact = artifact
        self.other = kwargs
        self._files_expanded = None     # set of all source files without globs
        self._exclude_files_expanded = set()
        self.srcs = None                # final set of required source files

    @classmethod
    def from_dict(cls, target_dict):
        return Target(**target_dict)

    def check(self):
        if self.artifact and self.artifact['type'] is 'deb':
            if not is_installed('fpm'):
                logger.error('fpm not installed; %s cannot be assembled',
                             self.artifact['name'])
                return 1
        return 0

    def flatten(self, lists):
        elements = []

        for l in lists:
            if isinstance(l, (list, tuple)):
                elements.extend(self.flatten(l))
            else:
                elements.append(l)

        return elements

    def hydrate(self):
        self._files_expanded = [glob(file_glob) for file_glob in self.files]
        self._files_expanded = self.flatten(self._files_expanded)
        self._files_expanded = set(self._files_expanded)

        if self.exclude_files:
            self._exclude_files_expanded = [
                glob(exclude_glob)
                for exclude_glob in self._exclude_files_expanded
            ]
            self._exclude_files_expanded = self.flatten(
                self._exclude_files_expanded
            )
            self._exclude_files_expanded = set(self._exclude_files_expanded)

        self.srcs = self._files_expanded - self._exclude_files_expanded


class TargetCollection(collections.Mapping):
    def __init__(self):
        self.target_dict = {}

    def add(self, target):
        name = target['name']
        if name in self.target_dict:
            raise DuplicateTargetError(
                "Target '%s' defined more than once" % name
            )
        self.target_dict[name] = Target.from_dict(target)

    def __getitem__(self, name):
        return self.target_dict[name]

    def __len__(self):
        return len(self.target_dict)

    def __iter__(self):
        for target in self.target_dict:
            yield target


Targets = TargetCollection()


class BuildFile(object):
    def __init__(self, path):
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
        for root, dirs, files in os.walk(directory, topdown=True):
            dirs[:] = [d for d in dirs if not d[0] == '.']
            logger.debug("Checking %s for build files", root)
            if 'BUILD' in files:
                buildFile = BuildFile(os.path.join(root, 'BUILD'))
                logger.debug("Found build file in %s", buildFile.dir)
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
        # pylint: disable=W0611
        from fusilly.build_python import (  # noqa: F401
            python_artifact
        )
        self.find_build_files()
        if not self.builds:
            logging.error("Could not locate any BUILD files under %s",
                          self.project_root)
            sys.exit(1)

        cwd = os.getcwd()

        for buildFile in self.builds:
            os.chdir(buildFile.dir)
            logger.debug("Loading BUILD from %s", buildFile.dir)
            # pylint: disable=W0122
            exec(buildFile.source(), globals(), locals())

        os.chdir(cwd)


def add_target_subparser(cmd, argParser):
    subparsers = argParser.add_subparsers(dest='subparser_name',
                                          help='Project to build')
    for target in Targets.itervalues():
        subparsers.add_parser(target.name, help='%s %s' % (cmd, target.name))


def do_build(buildFiles, args):
    argParser = argparse.ArgumentParser(description='Build project')
    add_target_subparser('build', argParser)

    args = argParser.parse_args(args)

    target_name = args.subparser_name
    target = Targets.get(target_name)

    if target.check():
        sys.exit(1)
    logger.info("Building %s...", target.name)
    target.hydrate()

    if target.pip_requirements and False:
        Virtualenv.create(
            target.name,
            target.pip_requirements,
            os.path.join(buildFiles.project_root, ".virtualenv")
        )
    if target.artifact:
        fpm_options = target.artifact.get('fpm_options', None)
        Deb.create(
            target.artifact['name'],
            target.srcs,
            fpm_options
        )


def main():
    COMMANDS = {
        'build': do_build,
    }

    argParser = argparse.ArgumentParser(description='Build and bundle')
    argParser.add_argument('command', choices=COMMANDS)
    argParser.add_argument('--logging', choices=['info', 'warn', 'debug'],
                           help='log level', default='debug')
    argParser.add_argument('args', nargs=argparse.REMAINDER)
    args = argParser.parse_args()

    logger.setLevel(args.logging.upper())

    buildFiles = BuildFiles()
    buildFiles.load()

    if not Targets:
        logger.error("No targets found")
        sys.exit(1)

    COMMANDS[args.command](buildFiles, args.args)


if __name__ == '__main__':
    main()
