import distutils.spawn


def is_iterable(var):
    if isinstance(var, (list, tuple)):
        return True
    return False


def to_iterable(var):
    if is_iterable(var):
        return var
    if var is None:
        return []
    return [var]


def is_installed(executable):
    path = distutils.spawn.find_executable(executable)
    return path is not None


def filter_dict(dictionary, keys):
    """ Return a copy of dictionary without the specified keys. """
    keys = to_iterable(keys)
    return {k: v for k, v in dictionary.iteritems() if k not in keys}
