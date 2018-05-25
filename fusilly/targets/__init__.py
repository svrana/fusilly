from .targets import Target, Targets # noqa

#
# TODDO: these should all be added to the global namespace automatically
#
from .virtualenv import virtualenv_target   # noqa
from .artifact import artifact_target   # noqa
from .command import command_target     # noqa
from .phony import phony_target     # noqa
