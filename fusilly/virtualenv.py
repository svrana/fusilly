import os
import subprocess

from .exceptions import VirtualenvCreationFailure


class Virtualenv(object):
    def __init__(self, identifier, pip_requirements_files, path):
        self.id = identifier
        self.reqs = pip_requirements_files
        self.path = path

    def _prep(self):
        ret = subprocess.call(['rm', '-rf', '%s' % self.path])
        if ret != 0:
            raise VirtualenvCreationFailure(
                'Could not remove existing virtualenv at %s', self.path
            )

    def _create(self):
        ret = subprocess.call(
            ['python', '-m', 'virtualenv', '%s' % self.path]
        )
        if ret != 0:
            raise VirtualenvCreationFailure()

    def _load(self):
        pip = os.path.join(self.path, 'bin', 'pip')
        for req in self.reqs:
            subprocess.call([pip, 'install', '-r', req])

    @classmethod
    def create(cls, identifier, pip_requirements_files, virtualenv_path):
        virtualenv = Virtualenv(identifier, pip_requirements_files,
                                virtualenv_path)
        virtualenv._prep()
        virtualenv._create()
        virtualenv._load()
        return virtualenv
