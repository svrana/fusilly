import abc
import collections
import logging
import os
import re

from glob2 import glob

from fusilly.exceptions import (
    DuplicateTargetError,
    BuildConfigError,
    MissingTemplateValue
)
from fusilly.utils import (
    filter_dict,
    is_installed,
    to_iterable,
)

logger = logging.getLogger(__name__)


class TargetCollection(collections.Mapping):
    def __init__(self):
        self.target_dict = {}

    def add(self, target):
        if target.name in self.target_dict:
            raise DuplicateTargetError(
                "Target '%s' defined more than once" % target.name
            )
        self.target_dict[target.name] = target

    def __getitem__(self, name):
        return self.target_dict[name]

    def __len__(self):
        return len(self.target_dict)

    def __iter__(self):
        for target in self.target_dict:
            yield target

    def maybe_set_buildfile(self, buildFile):
        for target in self.target_dict.itervalues():
            target._maybe_set_buildfile(buildFile)


Targets = TargetCollection()


class Target(object):
    """ Base class for all targets. """
    def __init__(self, name, **kwargs):
        self.name = name

        # the buildfile from which this target originated. It is set after the
        # target is exec'd, i.e., prior to run() being called.
        self.buildFile = None

        # an optional list of dependencies. These are other targets that must
        # be run prior to the execution of this target.
        deps = kwargs.pop('deps', None)
        self.deps = to_iterable(deps)

        # legacy_name is unused internally, it is used to document the target
        self.legacy_name = kwargs.pop('legacy_name', None)
        self.custom_options = kwargs

        Targets.add(self)

    @abc.abstractmethod
    def run(self, inputdict):
        pass

    def _do_deps(self, inputdict):
        for depname in self.deps:
            target = Targets.get(depname)
            outputdict = target._do_deps(inputdict)
            if outputdict:
                inputdict.update(outputdict)
            outputdict = target.run(inputdict)
            if outputdict:
                inputdict.update(outputdict)

        return inputdict

    @classmethod
    def create(cls, *args, **kwargs):
        # I like to use this to construct each Target to split up validation
        # and object creation, but not required.
        pass

    def check(self):
        """ Optional override called prior to hydrate and run()
        Return 0 if target evaluation should continue otherwise program exits.
        """
        return 0

    def cleanup(self):
        """ Optional override that is called after entire build process is
        completed. Called in the success and failure cases. """
        pass

    def _cleanup(self):
        """ Internal method called to cleanup all targets. """
        self._dep_cleanup()
        self.cleanup()

    def _maybe_set_buildfile(self, buildFile):
        """ Internal method that associates this target with the buildFile
        where it was defined. This is ugly, but simple. """
        if self.buildFile is None:
            self.buildFile = buildFile

    def _dep_cleanup(self):
        for depname in self.deps:
            target = Targets.get(depname)
            target._dep_cleanup()
            target.cleanup()

    def _make_cmdline_substitions(self, argDict, options):
        pattern = re.compile(r'{{(\w+)}}')

        for key, _ in options.iteritems():
            while True:
                value = options[key]
                if isinstance(value, dict):
                    self._make_cmdline_substitions(argDict, value)
                    break

                value = str(options[key])
                match = pattern.search(value)
                if not match:
                    break

                replace_value = argDict.get(match.group(1))
                if replace_value is None:
                    err = "Found '{{%s}}' without a definition" % match.group(1)
                    raise MissingTemplateValue(err)

                start, end = match.span()
                options[key] = value[0:start] + str(replace_value) + value[end:]

    def _templating(self, cmdline_opts):
        # allow build command to use command-line passed values too
        if self.build:
            self.custom_options['build'] = self.build
        if self.artifact:
            self.custom_options['artifact'] = self.artifact

        self._make_cmdline_substitions(cmdline_opts, self.custom_options)

        self.build = self.custom_options.pop('build', None)
        self.artifact = self.custom_options.pop('artifact', None)

    def hydrate(self, args):
        cmdline_opts = filter_dict(args.__dict__, ['subparser_name', 'args'])
        self._templating(cmdline_opts)

# class Target(object):
#     def __init__(self, name, func, files, artifact, **kwargs):
#         self.name = name
#         self.files = self.flatten(to_iterable(files))

#         exclude_files = kwargs.pop('exclude_files', None)
#         self.exclude_files = self.flatten(to_iterable(exclude_files))
#         self.run = kwargs.pop('run', None)
#         # Unused except to map the new build files to the existing bob code,
#         # but we remove so it doesn't show up as a configuration option
#         self.legacy_name = kwargs.pop('legacy_name', None)
#         # Command to run that will  kick off the build, typically npm build,
#         # make, etc
#         self.build = kwargs.pop('build', None)
#         if self.build:
#             if not isinstance(self.build, dict):
#                 raise BuildConfigError("'build' must be a dictionary")
#             if not self.build.get('command'):
#                 raise BuildConfigError("'build' must contain a 'command' key")
#             if not self.build.get('directory'):
#                 self.build['directory'] = '.'

#         # Internal function that is called to do the work of the target
#         self.func = func

#         self.artifact = artifact
#         if not isinstance(self.artifact, dict):
#             raise BuildConfigError("'artifact' must be a dictionary")
#         if not self.artifact.get('name'):
#             raise BuildConfigError("'artifact' must contain a 'name' key")
#         if not self.artifact.get('type'):
#             raise BuildConfigError("'artifact' must contain a 'type' key")

#         self.virtualenv = kwargs.pop('virtualenv', None)
#         if self.virtualenv:
#             if not isinstance(self.virtualenv, dict):
#                 raise BuildConfigError("'virtualenv' must be a dictionary")
#             if not self.virtualenv.get('requirements'):
#                 raise BuildConfigError(
#                     "'virtualenv' must contain a 'requirements key'"
#                 )
#             if not self.virtualenv.get('target_directory'):
#                 raise BuildConfigError(
#                     "'virtualenv' must contain a 'target_directory' key"
#                 )

#             self.virtualenv['requirements'] = to_iterable(
#                 self.virtualenv['requirements']
#             )

#         self.custom_options = kwargs

#         self._files_expanded = None     # set of all source files without globs
#         self._exclude_files_expanded = set()
#         self.srcs = None                # final set of required source files
#         self.buildFile = None

#     @classmethod
#     def from_dict(cls, target_dict):
#         return Target(**target_dict)

#     def check(self):
#         if self.artifact and self.artifact['type'] is 'deb':
#             if not is_installed('fpm'):
#                 logger.error("fpm not installed; %s cannot be assembled",
#                              self.artifact['name'])
#                 logger.info("fpm installation instructions at http://fpm.readthedocs.io/en/latest/installing.html")
#                 return 1
#         return 0

#     def maybe_set_buildfile(self, buildFile):
#         if self.buildFile is None:
#             self.buildFile = buildFile
#             self._expand_paths()

#     def _expand_paths(self):
#         path = self.buildFile.dir
#         if self.virtualenv:
#             self.virtualenv['requirements'] = [
#                 os.path.join(path, req)
#                 for req in self.virtualenv['requirements']
#             ]
#         if self.build:
#             path = os.path.join(self.buildFile.dir, self.build['directory'])
#             self.build['directory'] = os.path.abspath(path)

#     def _globs(self):
#         previous_dir = os.getcwd()

#         # globs are relative to the directory of the BUILD file,
#         # so change to that directory before expansion
#         os.chdir(self.buildFile.dir)

#         self._files_expanded = [glob(file_glob) for file_glob in self.files]
#         self._files_expanded = self.flatten(self._files_expanded)
#         self._files_expanded = [os.path.abspath(f) for f in self._files_expanded]
#         self._files_expanded = set(self._files_expanded)

#         if self.exclude_files:
#             self._exclude_files_expanded = [
#                 glob(exclude_glob)
#                 for exclude_glob in self.exclude_files
#             ]
#             self._exclude_files_expanded = self.flatten(
#                 self._exclude_files_expanded
#             )
#             self._exclude_files_expanded = [
#                 os.path.abspath(f) for f in self._exclude_files_expanded
#             ]
#             self._exclude_files_expanded = set(self._exclude_files_expanded)

#         self.srcs = self._files_expanded - self._exclude_files_expanded

#         # preserve directory caller expects
#         os.chdir(previous_dir)

#     def _make_cmdline_substitions(self, argDict, options):
#         pattern = re.compile(r'{{(\w+)}}')

#         for key, _ in options.iteritems():
#             while True:
#                 value = options[key]
#                 if isinstance(value, dict):
#                     self._make_cmdline_substitions(argDict, value)
#                     break

#                 value = str(options[key])
#                 match = pattern.search(value)
#                 if not match:
#                     break

#                 replace_value = argDict.get(match.group(1))
#                 if replace_value is None:
#                     err = "Found '{{%s}}' without a definition" % match.group(1)
#                     raise MissingTemplateValue(err)

#                 start, end = match.span()
#                 options[key] = value[0:start] + str(replace_value) + value[end:]

#     def _templating(self, cmdline_opts):
#         # allow build command to use command-line passed values too
#         if self.build:
#             self.custom_options['build'] = self.build
#         if self.artifact:
#             self.custom_options['artifact'] = self.artifact

#         self._make_cmdline_substitions(cmdline_opts, self.custom_options)

#         self.build = self.custom_options.pop('build', None)
#         self.artifact = self.custom_options.pop('artifact', None)

#     def hydrate(self, args):
#         cmdline_opts = filter_dict(args.__dict__, ['subparser_name', 'args'])
#         self._templating(cmdline_opts)
#         self._globs()
