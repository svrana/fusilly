import os
import toml

from fusilly.exceptions import FusillyConfigError
from fusilly.repo import GitRepo
from fusilly.utils import to_iterable


FUSILLY_CONFIG = None


class Config(object):
    def __init__(self, project_root, toml_config=None):
        self.project_root = project_root
        self.config = toml_config or {}
        self.repo = GitRepo(project_root)

    def custom_target_path(self):
        custom_targets = self.config.get('custom_targets', {})
        directory = custom_targets.get('directory')
        if directory is None:
            return None
        if directory == 'fusilly':
            raise FusillyConfigError(
                'fusilly target directory cannot be named `fusilly`'
            )

        plugin_path = os.path.join(self.project_root, directory)
        if not os.path.isdir(plugin_path):
            raise FusillyConfigError(
                'fusilly target directory %s not exist or is not a directory' %
                directory
            )
        return plugin_path

    def target_import_format(self, module_name):
        target_path = self.custom_target_path()
        if target_path is None:
            return None
        target = os.path.join(target_path, module_name)

        relpath = target[len(os.environ['PYTHONPATH'])+1:]
        relpath = relpath.replace("/", ".")
        return relpath

    def ignore_paths(self):
        build_files = self.config.get('build_files', {})
        ignore_paths = build_files.get('ignore_paths')
        return to_iterable(ignore_paths)

    def repo_head_sha(self):
        """ Return the sha of the local HEAD. """
        return self.repo.head_sha()

    def repo_head_sha_short(self):
        return self.repo.head_sha_short()


def find_project_root():
    dirs = ['.git']

    cwd = os.getcwd()
    while cwd != '/':
        # config file can also indicate project root
        if os.path.isfile(os.path.join(cwd, '.fusilly.toml')):
            return cwd
        roots = [os.path.join(cwd, d) for d in dirs]
        for root in roots:
            if os.path.exists(root):
                return cwd

        cwd = os.path.abspath(os.path.join(cwd, '..'))

    raise Exception("could not locate project root")


def _load_fusilly_config():
    root = find_project_root()
    config = os.path.join(root, '.fusilly.toml')

    try:
        with open(config) as configfile:
            toml_config = toml.load(configfile, _dict=dict)
            return Config(root, toml_config)
    except IOError:
        return Config(root)


def get_fusilly_config():
    # pylint: disable=W0603
    global FUSILLY_CONFIG
    if FUSILLY_CONFIG is not None:
        return FUSILLY_CONFIG

    FUSILLY_CONFIG = _load_fusilly_config()
    return FUSILLY_CONFIG
