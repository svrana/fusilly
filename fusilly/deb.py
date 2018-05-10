import logging
import os
import subprocess

logger = logging.getLogger(__file__)


class Deb(object):
    def __init__(self, package_name, files, options, dir_mappings):
        self.package_name = package_name
        self.files = files
        self.options = options

        self.options_str = ""
        options_list = ["--%s=%s" % (k, v) for k, v in options.iteritems()]
        self.options_str = ' '.join(options_list)
        self.dir_mappings = dir_mappings

    @classmethod
    def create(cls, package_name, target_directory, files, options,
               dir_mappings):
        deb = Deb(package_name, files, options, dir_mappings)
        files = ["%s=%s" % (file, os.path.join(target_directory, file))
                 for file in files]
        files_str = ' '.join(files)
        dir_mappings = ' '.join(dir_mappings)
        cmd = 'fpm -t deb %s -n %s -s dir %s %s' % (
            deb.options_str, package_name, dir_mappings, files_str
        )
        cmd_array = cmd.split(' ')
        logger.debug("Running: %s", cmd)
        subprocess.call(cmd_array)
        return deb
