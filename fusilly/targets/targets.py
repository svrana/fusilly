import collections
import logging
import os
import tempfile
import shutil

from glob2 import glob

from fusilly.deb import Deb
from fusilly.exceptions import (
    DuplicateTargetError,
    BuildConfigError,
    BuildError,
)
from fusilly.virtualenv import Virtualenv
from fusilly.utils import to_iterable, is_installed

logger = logging.getLogger(__file__)


class Target(object):
    def __init__(self, name, func, files, exclude_files, artifact, virtualenv,
                 **kwargs):
        self.name = name
        self.files = self.flatten(to_iterable(files))
        self.exclude_files = self.flatten(to_iterable(exclude_files))
        self.run = kwargs.pop('run', None)
        # Unused except to map the new build files to the existing bob code,
        # but we remove so it doesn't show up as a configuration option
        self.legacy_name = kwargs.pop('legacy_name', None)
        # Command to run that will  kick off the build, typically npm build,
        # make, etc
        self.build = kwargs.pop('build', None)
        # Internal function that is called to do the work of the target
        self.func = func

        self.artifact = artifact
        if not isinstance(self.artifact, dict):
            raise BuildConfigError("artifact must be a dictionary")
        if not self.artifact.get('name'):
            raise BuildConfigError("artifact must contain a 'name' key")
        if not self.artifact.get('type'):
            raise BuildConfigError("artifact must contain a 'type' key")

        self.virtualenv = virtualenv
        if virtualenv:
            if not isinstance(virtualenv, dict):
                raise BuildConfigError('virtualenv must be a dictionary')
            if not virtualenv.get('requirements'):
                raise BuildConfigError(
                    "virtualenv must contain a 'requirements key'"
                )
            if not virtualenv.get('target_directory'):
                raise BuildConfigError(
                    "virtualenv must contain a 'target_directory' key"
                )

            self.virtualenv['requirements'] = to_iterable(
                self.virtualenv['requirements']
            )

        self.custom_options = kwargs

        self._files_expanded = None     # set of all source files without globs
        self._exclude_files_expanded = set()
        self.srcs = None                # final set of required source files
        self.buildFile = None

    @classmethod
    def from_dict(cls, target_dict):
        return Target(**target_dict)

    def check(self):
        if self.artifact and self.artifact['type'] is 'deb':
            if not is_installed('fpm'):
                logger.error("fpm not installed; %s cannot be assembled",
                             self.artifact['name'])
                logger.info("fpm installation instructions at http://fpm.readthedocs.io/en/latest/installing.html")
                return 1
        return 0

    def maybe_set_buildfile(self, buildFile):
        if self.buildFile is None:
            self.buildFile = buildFile
            self._expand_paths()

    def _expand_paths(self):
        path = self.buildFile.dir
        if self.virtualenv:
            self.virtualenv['requirements'] = [
                os.path.join(path, req)
                for req in self.virtualenv['requirements']
            ]

    def flatten(self, lists):
        elements = []

        for l in lists:
            if isinstance(l, (list, tuple)):
                elements.extend(self.flatten(l))
            else:
                elements.append(l)

        return elements

    def hydrate(self):
        previous_dir = os.getcwd()

        # globs are relative to the directory of the BUILD file,
        # so change to that directory before expansion
        os.chdir(self.buildFile.dir)

        self._files_expanded = [glob(file_glob) for file_glob in self.files]
        self._files_expanded = self.flatten(self._files_expanded)
        self._files_expanded = [os.path.abspath(f) for f in self._files_expanded]
        self._files_expanded = set(self._files_expanded)

        if self.exclude_files:
            self._exclude_files_expanded = [
                glob(exclude_glob)
                for exclude_glob in self.exclude_files
            ]
            self._exclude_files_expanded = self.flatten(
                self._exclude_files_expanded
            )
            self._exclude_files_expanded = [os.path.abspath(f) for f in self._exclude_files_expanded]
            self._exclude_files_expanded = set(self._exclude_files_expanded)

        self.srcs = self._files_expanded - self._exclude_files_expanded

        # preserve directory caller expects
        os.chdir(previous_dir)


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

    def maybe_set_buildfile(self, buildFile):
        for target in self.target_dict.itervalues():
            target.maybe_set_buildfile(buildFile)


def _python_artifact_bundle(buildFiles, target, programArgs):
    try:
        dir_mappings = []
        tempdir = tempfile.mkdtemp(prefix='fusilly-')
        if target.virtualenv and not programArgs.skip_virtualenv:
            logger.info("Installing %s deps into virtualenv",
                        ' '.join(target.virtualenv['requirements']))
            Virtualenv.create(
                target.name,
                target.virtualenv['requirements'],
                tempdir,
            )
            logging.info("virtualenv creation complete")

            dir_mappings.append(
                '%s=%s' % (tempdir, target.virtualenv['target_directory'])
            )

        if target.artifact and not programArgs.skip_artifact:
            logger.info("Bundling %s", target.name)
            fpm_options = target.artifact.get('fpm_options', None)
            Deb.create(
                buildFiles.project_root,
                target.artifact['name'],
                target.artifact['target_directory'],
                target.srcs,
                fpm_options,
                dir_mappings
            )
            logging.info("Bundling complete")
    except BuildError:
        logger.error('Cannot continue; build failed')
        raise
    finally:
        logger.info("removing temporary directory %s", tempdir)
        shutil.rmtree(tempdir)


def python_artifact(name, files=None, exclude_files=None, artifact=None,
                    virtualenv=None, **kwargs):
    if not artifact:
        raise BuildConfigError(
            "build target of type %s must specify an 'artifact'", name
        )

    Targets.add(dict(
        func=_python_artifact_bundle,
        name=name,
        files=files,
        exclude_files=exclude_files,
        virtualenv=virtualenv,
        artifact=artifact,
        **kwargs
    ))


Targets = TargetCollection()
