import logging
import os

from glob2 import glob

from fusilly.deb import Deb
from fusilly.exceptions import BuildConfigError
from fusilly.utils import flatten, is_installed, to_iterable
from .targets import Target


logger = logging.getLogger(__name__)


class ArtifactTarget(Target):
    def _globs(self):
        previous_dir = os.getcwd()

        # globs are relative to the directory of the BUILD file,
        # so change to that directory before expansion
        os.chdir(self.buildFile.dir)

        files_expanded = [glob(file_glob) for file_glob in self.files]
        files_expanded = flatten(files_expanded)
        files_expanded = set([os.path.abspath(f) for f in files_expanded])

        if self.exclude_files:
            exclude_files_expanded = [
                glob(exclude_glob) for exclude_glob in self.exclude_files
            ]
            exclude_files_expanded = flatten(exclude_files_expanded)
            exclude_files_expanded = [
                os.path.abspath(f) for f in exclude_files_expanded
            ]
            exclude_files_expanded = set(exclude_files_expanded)
        else:
            exclude_files_expanded = set()

        # pylint: disable=W0201
        self.srcs = files_expanded - exclude_files_expanded

        # preserve directory caller expects
        os.chdir(previous_dir)

    def _get_dir_mappings(self, inputdict):
        if 'artifact_target_dir_mappings' not in inputdict:
            return []

        expanded_mappings = []

        dir_mappings = to_iterable(inputdict['artifact_target_dir_mappings'])
        for dir_mapping in dir_mappings:
            source_dir, target_dir = dir_mapping.split('=')
            if not target_dir.startswith('/'):
                target_dir = os.path.join(self.target_directory, target_dir)
            expanded_mappings.append("%s/=%s" % (source_dir, target_dir))

        return expanded_mappings

    def check(self):
        if self.artifact_type is 'deb':
            if not is_installed('fpm'):
                logger.error("fpm not installed; %s cannot be assembled",
                             self.artifact['name'])
                logger.info("fpm installation instructions at http://fpm.readthedocs.io/en/latest/installing.html")
                return 1
        return 0

    def run(self, inputdict):
        self._globs()
        dir_mappings = self._get_dir_mappings(inputdict)

        Deb.create(
            self.buildFile.project_root,
            self.name,
            self.target_directory,
            self.srcs,
            self.fpm_options,
            dir_mappings
        )
        logging.info("Bundling complete")

    @classmethod
    def create(cls, name, files, artifact_type, target_directory, fpm_options,
               exclude_files=None, **kwargs):
        target = ArtifactTarget(name, **kwargs)
        # pylint: disable=W0201
        target.target_directory = target_directory
        target.artifact_type = artifact_type
        target.fpm_options = fpm_options
        target.files = to_iterable(files)
        target.exclude_files = to_iterable(exclude_files)
        target.srcs = None

        return target


def artifact_target(name, **kwargs):
    if 'files' not in kwargs:
        raise BuildConfigError(
            "artifact_target %s must contain a 'files' key" % name
        )
    if 'artifact' not in kwargs:
        raise BuildConfigError(
            "artifact_target %s must contain an 'artifact' dictionary" % name
        )
    artifact = kwargs.pop('artifact')
    if not isinstance(artifact, dict):
        raise BuildConfigError(
            "artifact of artifact_target %s must be a "
            "dictionary" % name
        )

    if 'type' not in artifact:
        raise BuildConfigError(
            "artifact_target %s must contain a 'type' key" % name
        )

    if 'target_directory' not in artifact:
        raise BuildConfigError(
            "artifact_target %s must contain a 'target_directory' key" % name
        )
    if artifact['type'] not in ['deb']:
        raise BuildConfigError('Sorry, only .deb artifacts are supported')

    if 'fpm_options' not in artifact:
        raise BuildConfigError(
            "artifact_target %s must contain a 'fpm_options' dictionary" % name
        )
    opts = artifact['fpm_options']
    if 'deb-user' not in opts:
        raise BuildConfigError(
            "fpm_options dictionary of %s target must contain "
            "a 'deb-user' key" % name
        )
    if 'deb-group' not in opts:
        raise BuildConfigError(
            "fpm_options dictionary of %s target must contain a "
            "'deb-group' key" % name
        )
    if 'maintainer' not in opts:
        raise BuildConfigError(
            "fpm_options dictionary of %s target must contain a "
            "'maintiner' key" % name
        )

    return ArtifactTarget.create(
        name,
        kwargs.pop('files'),
        artifact_type=artifact['type'],
        target_directory=artifact['target_directory'],
        fpm_options=artifact['fpm_options'],
        **kwargs
    )
