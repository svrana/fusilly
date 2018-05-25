import logging

from fusilly.exceptions import BuildConfigError
from .targets import Target


logger = logging.getLogger(__name__)


class Phony(Target):
    def run(self, _):
        return None


def phony_target(name, **kwargs):
    if 'deps' not in kwargs:
        raise BuildConfigError('phony_target %s without deps does nothing' % name)
    if not kwargs['deps']:
        raise BuildConfigError('phony_target %s without an empty deps list does nothing' % name)

    return Phony(name, **kwargs)
