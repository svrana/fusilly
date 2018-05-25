import abc
import collections
import logging
import re

from fusilly.exceptions import (
    DuplicateTargetError,
    MissingTemplateValue
)
from fusilly.utils import (
    filter_dict,
    to_iterable,
    classname,
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

    # Any variable name in the list below can use templates such that users can
    # substitute values for the templates on the command line.
    TEMPLATE_ATTRS = []

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

    def _dep_check(self):
        for depname in self.deps:
            target = Targets.get(depname)
            target._dep_check()
            target.check()

    def _check(self):
        """ Internal method called to cleanup all targets. """
        self._dep_check()
        self.check()

    def _dep_cleanup(self):
        for depname in self.deps:
            target = Targets.get(depname)
            target._dep_cleanup()
            target.cleanup()

    def _cleanup(self):
        """ Internal method called to cleanup all targets. """
        self._dep_cleanup()
        self.cleanup()

    def _maybe_set_buildfile(self, buildFile):
        """ Internal method that associates this target with the buildFile
        where it was defined. This is ugly, but simple. """
        if self.buildFile is None:
            self.buildFile = buildFile

    def _run(self, programArgs, inputdict):
        """ Internal implementation; do not override. Run the target, running
        each of its dependencies first and passes the combined output of each
        dep to the next dependency.
        """
        for depname in self.deps:
            target = Targets.get(depname)
            target._hydrate(programArgs)
            outputdict = target._run(programArgs, inputdict)
            if outputdict:
                inputdict.update(outputdict)

        self._hydrate(programArgs)
        logger.info("Running target %s:%s",
                    classname(self).split('.')[-1], self.name)
        outputdict = self.run(inputdict)
        if outputdict:
            inputdict.update(outputdict)
        return inputdict

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
        for template_attr in self.TEMPLATE_ATTRS:
            if template_attr not in self.__dict__:
                logging.error("template attr '%s' does not exist in template %s",
                              template_attr, self.name)
            # potential for clobbering here, should probably dunder
            self.custom_options[template_attr] = self.__dict__.get(template_attr)

        self._make_cmdline_substitions(cmdline_opts, self.custom_options)

        for template_attr in self.TEMPLATE_ATTRS:
            self.__dict__[template_attr] = self.custom_options.pop(template_attr)

    def _hydrate(self, args):
        cmdline_opts = filter_dict(args.__dict__, ['subparser_name', 'args'])
        self._templating(cmdline_opts)
