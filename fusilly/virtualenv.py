import os

from .command import Command
from .exceptions import VirtualenvCreationFailure


class Virtualenv(object):
    def __init__(self, identifier, pip_requirements_files, path):
        self.id = identifier
        self.reqs = pip_requirements_files
        self.path = path

    def _create(self):
        cmd = 'python -m virtualenv %s' % self.path
        ret = Command(cmd).run()
        if ret != 0:
            raise VirtualenvCreationFailure()

    def _load(self):
        pip = os.path.join(self.path, 'bin', 'pip')
        for req in self.reqs:
            cmd = '%s install -r %s' % (pip, req)
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
