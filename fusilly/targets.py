import collections
import logging
import os

from glob2 import glob

from fusilly.exceptions import DuplicateTargetError, BuildConfigError
from fusilly.utils import to_iterable, is_installed

logger = logging.getLogger(__file__)


class Target(object):
    def __init__(self, name, files, exclude_files=None, pip_requirements=None,
                 artifact=None, **kwargs):
        self.name = name
        self.files = self.flatten(to_iterable(files))
        self.exclude_files = self.flatten(to_iterable(exclude_files))
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
        self.pip_requirements = [
                os.path.join(path, req) for req in self.pip_requirements
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


def python_artifact(name, files=None, artifact=None, pip_requirements=None,
                    exclude_files=None,
                    **kwargs):
    if not artifact:
        raise BuildConfigError(
            "build target %s must specify an 'artifact'", name
        )

    Targets.add(dict(
        func='make build',
        name=name,
        files=files,
        artifact=artifact,
        pip_requirements=pip_requirements,
        exclude_files=exclude_files,
        **kwargs
    ))


Targets = TargetCollection()
