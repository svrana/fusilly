import os

from .command import Command
from .exceptions import VirtualenvCreationFailure


class Virtualenv(object):
    def __init__(self, identifier, requirements_file, path):
        self.id = identifier
        self.reqs = requirements_file
        self.path = path

    def update_local(self):
        """On some systems virtualenv has a local directory that symlinks back
        to itself with the full path.  Replace this relative directories so
        links will continue working when unpacked to target directory.

        Credit: https://github.com/fireteam/virtualenv-tools/blob/master/virtualenv_tools.py#L125
        """
        local_dir = os.path.join(self.path, 'local')
        if not os.path.isdir(local_dir):
            return

        for folder in 'bin', 'lib', 'include':
            filename = os.path.join(local_dir, folder)
            target = '../%s' % folder
            if os.path.islink(filename) and os.readlink(filename) != target:
                os.remove(filename)
                os.symlink('../%s' % folder, filename)

    def update_links(self):
        """ Unfortunate hacks around virtualenv's inability to create a relocatable
        virtualenv. """
        self.update_local()

        # distutils link pointing in to fusilly virtualenv for some reason :(
        # move it to where distutils is placed by libpython2.7-stdlib
        distutils = os.path.join(self.path, 'lib', 'python2.7', 'distutils')
        if not os.path.islink(distutils):
            return
        target = '/usr/lib/python2.7/distutils'
        if os.readlink(distutils) != target:
            os.remove(distutils)
            os.symlink(target, distutils)

    def _create(self):
        ret = Command('virtualenv --distribute %s' % self.path).run()
        if ret != 0:
            raise VirtualenvCreationFailure()

        self.update_links()

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
