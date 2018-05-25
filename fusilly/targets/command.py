import logging

from fusilly.command import Command as Cmd
from fusilly.exceptions import BuildConfigError, CommandTargetRunFailure
from .targets import Target


logger = logging.getLogger(__name__)


class Command(Target):
    TEMPLATE_ATTRS = ['command']

    def run(self, _):
        ret = Cmd(self.command, self.directory).run()
        if ret != 0:
            raise CommandTargetRunFailure()
        return None

    @classmethod
    def create(cls, name, command, directory=None, **kwargs):
        target = Command(name, **kwargs)
        # pylint: disable=W0201
        target.command = command
        target.directory = directory  # needs templating/expansion for relative


def command_target(name, **kwargs):
    if 'command' not in kwargs:
        raise BuildConfigError(
            "command_target %s must contain a 'command' key" % name
        )

    return Command.create(
        name,
        kwargs.pop('command'),
        directory=kwargs.pop('directory', None),
        **kwargs
    )
