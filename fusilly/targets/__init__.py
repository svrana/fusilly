
import os
import imp
from importlib import import_module
import sys

from fusilly.config import get_fusilly_config

from .targets import Target, Targets # noqa


def load_internal_targets():
    """ Load plugins from plugins/ directory in this repository. This could be
    done with imports, but I got silly on it. Feel free to change.
    """
    cdir = os.path.abspath(os.path.dirname(__file__))

    IGNORE_LIST = [
        '__init__.py',
        'targets.py',
    ]

    modules = [
        f.split('.')[0] for f in os.listdir(cdir)
        if os.path.isfile(os.path.join(cdir, f)) and
        f not in IGNORE_LIST and f.endswith('.py')
    ]

    for module_name in modules:
        func_name = "%s_target" % module_name
        module = import_module('.%s' % module_name, 'fusilly.targets')
        target_func = getattr(module, func_name)
        if target_func:
            setattr(sys.modules['fusilly.targets'], func_name, target_func)


def load_external_targets():
    """ Load user specified targets from the configured target directory. """
    config = get_fusilly_config()
    plugin_path = config.custom_target_path()
    if plugin_path:
        modules = [
            f.split('.')[0] for f in os.listdir(plugin_path)
            if os.path.isfile(os.path.join(plugin_path, f)) and
            f not in ['__init__.py'] and f.endswith('.py')
        ]

        for module_name in modules:
            f, file, desc = imp.find_module(module_name, [plugin_path])
            module = imp.load_module(module_name, f, file, desc)
            func_name = "%s_target" % module_name
            target_func = getattr(module, func_name)
            if target_func:
                setattr(sys.modules['fusilly.targets'], func_name, target_func)


load_internal_targets()
load_external_targets()
