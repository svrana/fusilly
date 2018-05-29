import os
import toml


FUSILLY_CONFIG = None


def _load_fusilly_config():
    dirs = ['.git']

    cwd = os.getcwd()
    while cwd != '/':
        roots = [os.path.join(cwd, d) for d in dirs]
        for root in roots:
            if os.path.exists(root):
                try:
                    with open('.fusilly.toml') as config:
                        return toml.load(config, _dict=dict)
                except IOError:
                    return {}

        cwd = os.path.abspath(os.path.join(cwd, '..'))

    return None


def get_fusilly_config():
    # pylint: disable=W0603
    global FUSILLY_CONFIG
    if FUSILLY_CONFIG is not None:
        return FUSILLY_CONFIG

    FUSILLY_CONFIG = _load_fusilly_config()
    return FUSILLY_CONFIG
