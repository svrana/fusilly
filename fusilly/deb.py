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

        with NamedTemporaryFile(prefix='%s-includes-' % package_name) as f:
            deb = Deb(package_name, files, options, dir_mappings)
            # these should be files only, fpm will create the directories for us if we need
            # them. If you want an empty dir, has to be in dir_mappinmgs
            files = ["%s=%s" % (filename, os.path.join(target_directory, filename))
                     for filename in files if not os.path.isdir(filename)]
            files_str = '\n'.join(files)
            dir_mappings = ' '.join(dir_mappings)
            f.write(files_str)
            f.flush()
            # try to ensure that content is on disk before fpm tries to read it
            os.fsync(f.fileno())
            cmd = 'fpm -t deb {user_options} -n {package_name} -s dir ' \
                  '--inputs {src_input} {dir_mappings}'.format(
                    user_options=deb.options_str,
                    package_name=package_name,
                    src_input=f.name,
                    dir_mappings=dir_mappings,
                  )
            cmd_array = cmd.split(' ')
            logger.debug("Running: %s", cmd)
            subprocess.call(cmd_array)
            return deb
