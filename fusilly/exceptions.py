class FusillyBaseException(Exception):
    pass


class BuildConfigError(FusillyBaseException):
    pass


class BuildError(FusillyBaseException):
    pass


class DuplicateTargetError(BuildConfigError):
    pass


class VirtualenvCreationFailure(BuildError):
    pass


class DebCreationFailure(BuildError):
    pass


class UserSuppliedBuildCmdFailure(BuildError):
    pass


class MissingTemplateValue(BuildError):
    pass

class CommandTargetRunFailure(BuildError):
    pass
