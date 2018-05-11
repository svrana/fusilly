import logging
import os
import subprocess
from tempfile import NamedTemporaryFile


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
        # bzip compresses better, but takes a little longer
        if not 'deb-compression' in options:
            options['deb-compression'] = 'bzip2'

        with NamedTemporaryFile(prefix='includes') as f:
            deb = Deb(package_name, files, options, dir_mappings)
            # these should be files only, fpm will create the directories for us if we need
            # them. If you want an empty dir, has to be in dir_mappinmgs
            files = ["%s=%s" % (file, os.path.join(target_directory, file))
                     for file in files if os.path.isdir(file)]
            files_str = '\n'.join(files)
            dir_mappings = ' '.join(dir_mappings)
            f.write(files_str)
            f.flush()
            cmd = 'fpm -t deb %s -n %s -s dir --inputs %s %s' % (
                deb.options_str, package_name, '/home/shaw/include-files.txt', dir_mappings
            )
            cmd_array = cmd.split(' ')
            logger.debug("Running: %s", cmd)
            subprocess.call(cmd_array)
            return deb
