import logging
import os
import tempfile
import shutil

from fusilly.virtualenv import Virtualenv
from fusilly.exceptions import BuildConfigError
from .targets import Target


logger = logging.getLogger(__name__)


class VirtualenvTarget(Target):
    def _expand_paths(self):
        # pylint: disable=W0201
        self.requirements = os.path.join(
            self.buildFile.dir, self.requirements
        )

    def run(self, inputdict):
        self._expand_paths()

        # pylint: disable=W0201
        self.tempdir = tempfile.mkdtemp(prefix='fusilly-%s-' % self.name)
        logger.info("Installing %s deps into virtualenv", self.requirements)

        Virtualenv.create(
            self.name,
            self.requirements,
            self.tempdir,
        )
        logging.info("virtualenv creation complete")

        dirmap = "%s=%s" % (self.tempdir, self.target_directory_name)
        return dict(artifact_target_dir_mappings=dirmap)

    @classmethod
    def create(cls, name, requirements, target_directory, **kwargs):
        target = VirtualenvTarget(name, **kwargs)
        # pylint: disable=W0201
        target.requirements = requirements
        target.target_directory_name = target_directory
        target.tempdir = None

        return target

    def cleanup(self):
        if self.tempdir:
            logger.debug("removing temporary directory %s", self.tempdir)
            #shutil.rmtree(self.tempdir)


def virtualenv_target(name, **kwargs):
    if 'requirements' not in kwargs:
        raise BuildConfigError(
            "virtualenv_target must contain a 'requirements' key"
        )
    if 'target_directory_name' not in kwargs:
        raise BuildConfigError(
            "virtualenv_target must contain a 'target_directory_name' key"
        )

    return VirtualenvTarget.create(
        name,
        kwargs.pop('requirements'),
        kwargs.pop('target_directory_name'),
        **kwargs
    )
