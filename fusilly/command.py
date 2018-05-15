import os
import logging
import subprocess

logger = logging.getLogger(__name__)


class Command(object):
    def __init__(self, command, directory=None):
        self.command = command
        self.directory = directory

    def run(self):
        if self.directory:
            last_directory = os.getcwd()
            os.chdir(self.directory)
        else:
            last_directory = None

        logger.info("Running command: %s", self.command)
        cmd = self.command.split(' ')
        ret = subprocess.call(cmd)

        if last_directory:
            os.chdir(last_directory)

        return ret
