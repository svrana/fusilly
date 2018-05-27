from .targets import Target, Targets # noqa

import os
from importlib import import_module
import sys

# This is hear so that additional targets need not import them manually.
# But it's pretty silly
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
    setattr(sys.modules['fusilly.targets'], func_name, target_func)
