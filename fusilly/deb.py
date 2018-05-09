import logging
import subprocess

logger = logging.getLogger(__file__)


class Deb(object):
    def __init__(self, package_name, files, options):
        self.package_name = package_name
        self.files = files
        self.options = options

        self.options_str = ""
        options_list = ["--%s=%s" % (k, v) for k, v in options.iteritems()]
        self.options_str = ' '.join(options_list)

    @classmethod
    def create(cls, package_name, files, options):
        deb = Deb(package_name, files, options)
        files_str = ' '.join(files)
        cmd = 'fpm -C /home/shaw/Projects/fusilly/fusilly -t deb %s -n %s -s dir %s' % (
            deb.options_str, package_name, files_str
        )
        cmd_array = cmd.split(' ')
        logger.debug("Running: %s", cmd)
        subprocess.call(cmd_array)
        return deb
