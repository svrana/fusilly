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


def flatten(lists):
    """ Turn any number of embedded lists and returns one list with all
    elements of sub-lists. """
    elements = []

    for l in lists:
        if isinstance(l, (list, tuple)):
            elements.extend(flatten(l))
        else:
            elements.append(l)

    return elements


def classname(klass):
    return klass.__module__ + "." + klass.__class__.__name__
