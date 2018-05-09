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
