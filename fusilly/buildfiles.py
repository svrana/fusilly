import os
import json     # noqa
import logging
import sys

from fusilly.config import get_fusilly_config
from fusilly.targets import Targets
# Import all the targets so that the build files can find them when exec'd
from fusilly.targets import *   # noqa


logger = logging.getLogger(__name__)


class BuildFile(object):
    def __init__(self, project_root, path):
        self.project_root = project_root
        self.path = path
        self.dir = os.path.dirname(path)
        self._source = None

    def source(self):
        if self._source is None:
            with open(self.path, 'r') as buildfile:
                self._source = buildfile.read()
        return self._source


class BuildFiles(object):
    """ A collection of BuildFiles that is able to locate all the BUILD files
    of a project. """
    def __init__(self):
        self.project_root = None
        self.builds = []

    def find_build_files_in(self, directory):
        builds = []
        ignore_paths = get_fusilly_config().ignore_paths()

        for root, dirs, files in os.walk(directory, topdown=True):
            # skip over hidden directories...
            # skip over the case where go has brought in deps that contain
            # their own BUILD files.
            dirs[:] = [d for d in dirs if not d[0] == '.' or
                       d in ignore_paths]
            logger.debug("Checking %s for build files", root)
            if 'BUILD' in files:
                buildFilePath = os.path.join(root, 'BUILD')
                buildFile = BuildFile(self.project_root, buildFilePath)
                logger.debug("Found %s", buildFilePath)
                builds.append(buildFile)
        return builds

    def find_build_files(self):
        self.project_root = get_fusilly_config().project_root
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
            exec(buildFile.source())

            # We don't know which targets were just loaded, but we need each
            # one to know which buildFile its associated with.
            # TODO: should be able to pass this in the environment during exec
            # and grab it from there.
            Targets.maybe_set_buildfile(buildFile)

        if not Targets:
            logger.error("No targets found")
            sys.exit(1)
