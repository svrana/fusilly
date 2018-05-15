import logging
import os
import subprocess
from tempfile import NamedTemporaryFile

from fusilly.exceptions import DebCreationFailure


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

    def create_mapping(self, project_root, target_directory, files):
        srcs = []

        for filename in files:
            destination = os.path.join(
                target_directory,
                filename[len(project_root)+1:]
            )
            srcs.append("%s=%s" % (filename, destination))

        return srcs

    def write_mapping(self, fd, srcs):
        files_str = '\n'.join(srcs) # fpm expects src=dst, one per line

        fd.write(files_str)
        fd.flush()

        # try to ensure that content is on disk before fpm tries to read it
        os.fsync(fd.fileno())

    @classmethod
    def create(cls, project_root, package_name, target_directory, files,
               options, dir_mappings):
        # bzip compresses better, but takes a little longer
        if 'deb-compression' not in options:
            options['deb-compression'] = 'bzip2'

        with NamedTemporaryFile(prefix='%s-includes-' % package_name) as f:
            deb = Deb(package_name, files, options, dir_mappings)
            srcs = deb.create_mapping(project_root, target_directory, files)
            deb.write_mapping(f, srcs)

            cmd = 'fpm -t deb {user_options} -n {package_name} -s dir ' \
                  '--inputs {src_input}'.format(
                    user_options=deb.options_str,
                    package_name=package_name,
                    src_input=f.name
                  )
            if dir_mappings:
                cmd += ' %s' % ' '.join(dir_mappings)

            cmd_array = cmd.split(' ')
            logger.debug("Running: %s", cmd)
            ret = subprocess.call(cmd_array)
            if ret:
                raise DebCreationFailure()
            return deb
