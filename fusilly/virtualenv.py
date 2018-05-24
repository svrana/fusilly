import os

from .command import Command
from .exceptions import VirtualenvCreationFailure


class Virtualenv(object):
    def __init__(self, identifier, requirements_file, path):
        self.id = identifier
        self.reqs = requirements_file
        self.path = path

    def _create(self):
        cmd = 'python -m virtualenv %s' % self.path
        ret = Command(cmd).run()
        if ret != 0:
            raise VirtualenvCreationFailure()

    def _load(self):
        pip = os.path.join(self.path, 'bin', 'pip')
        cmd = '%s install -r %s' % (pip, self.reqs)
        ret = Command(cmd).run()
        if ret != 0:
            raise VirtualenvCreationFailure()

    @classmethod
    def create(cls, identifier, pip_requirements_files, virtualenv_path):
        virtualenv = Virtualenv(identifier, pip_requirements_files,
                                virtualenv_path)
        virtualenv._create()
        virtualenv._load()
        return virtualenv
