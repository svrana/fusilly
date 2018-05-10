#!/usr/bin/env python

import argparse
import os
import os.path
import logging
import sys
import shutil
import tempfile


from fusilly.deb import Deb
# pylint: disable=W0611
from fusilly.targets import Targets, python_artifact    # noqa
from fusilly.virtualenv import Virtualenv


stream_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
stream_handler.setFormatter(formatter)
root_logger = logging.getLogger('')
root_logger.addHandler(stream_handler)
logger = logging.getLogger(__file__)


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
                buildFilePath = os.path.join(root, 'BUILD')
                buildFile = BuildFile(buildFilePath)
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

    if target.pip_requirements:
        tempdir = tempfile.mkdtemp()
        try:
            virtualenv_path = os.path.join(
                tempdir, "virtualenv"
            )

            Virtualenv.create(
                target.name,
                target.pip_requirements,
                virtualenv_path
            )
            #target.add_virtualenv(virtualenv_path)

            if target.artifact:
                fpm_options = target.artifact.get('fpm_options', None)
                if target.pip_requirements:
                    ve_install_path = os.path.join(
                    target.artifact.get('target_directory')
                    )
                else:
                    ve_install_path = None

                Deb.create(
                    target.artifact['name'],
                    target.artifact['target_directory'],
                    target.srcs,
                    fpm_options,
                    dir_mappings=[
                        '%s=%s' % (virtualenv_path, ve_install_path),
                    ]
                )
        finally:
            shutil.rmtree(tempdir)


def main():
    COMMANDS = {
        'build': do_build,
    }

    argParser = argparse.ArgumentParser(description='Build and bundle')
    argParser.add_argument('command', choices=COMMANDS)
    argParser.add_argument('--logging', choices=['info', 'warn', 'debug'],
                           help='log level', default='info')
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
