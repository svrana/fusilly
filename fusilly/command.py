import os
import logging
import subprocess

logger = logging.getLogger(__name__)


class Command(object):
    def __init__(self, command, directory=None):
        self.command = command
        self.directory = directory

    def _run_inherit_stdout(self, cmd):
        ret = subprocess.call(cmd)
        return ret

    def _run_capture_stdout(self, cmd):
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, _ = process.communicate()
        return process.returncode, stdout

    def run(self, capture_stdout=False):
        if self.directory:
            last_directory = os.getcwd()
            os.chdir(self.directory)
        else:
            last_directory = None

        logger.info("Running command: %s", self.command)

        cmd = self.command.split(' ')
        if capture_stdout:
            ret, stdout = self._run_capture_stdout(cmd)
        else:
            ret = self._run_inherit_stdout(cmd)

        if last_directory:
            os.chdir(last_directory)

        if not capture_stdout:
            return ret

        return ret, stdout
