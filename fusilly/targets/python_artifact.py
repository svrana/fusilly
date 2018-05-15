import logging
import tempfile
import shutil

from fusilly.deb import Deb
from fusilly.exceptions import (
    BuildConfigError,
    BuildError,
)
from fusilly.virtualenv import Virtualenv

from .targets import Targets

logger = logging.getLogger(__file__)


def _python_artifact_bundle(buildFiles, target, programArgs):
    try:
        dir_mappings = []
        tempdir = tempfile.mkdtemp(prefix='fusilly-%s' % target.name)
        if target.virtualenv and not programArgs.skip_virtualenv:
            logger.info("Installing %s deps into virtualenv",
                        ' '.join(target.virtualenv['requirements']))
            Virtualenv.create(
                target.name,
                target.virtualenv['requirements'],
                tempdir,
            )
            logging.info("virtualenv creation complete")

            dir_mappings.append(
                '%s=%s' % (tempdir, target.virtualenv['target_directory'])
            )

        if target.artifact and not programArgs.skip_artifact:
            logger.info("Bundling %s", target.name)
            fpm_options = target.artifact.get('fpm_options', None)
            Deb.create(
                buildFiles.project_root,
                target.artifact['name'],
                target.artifact['target_directory'],
                target.srcs,
                fpm_options,
                dir_mappings
            )
            logging.info("Bundling complete")
    except BuildError:
        logger.error('Cannot continue; build failed')
        raise
    finally:
        logger.info("removing temporary directory %s", tempdir)
        shutil.rmtree(tempdir)


def python_artifact(name, files=None, exclude_files=None, artifact=None,
                    virtualenv=None, **kwargs):
    if not artifact:
        raise BuildConfigError(
            "build target of type %s must specify an 'artifact'", name
        )

    Targets.add(dict(
        func=_python_artifact_bundle,
        name=name,
        files=files,
        exclude_files=exclude_files,
        virtualenv=virtualenv,
        artifact=artifact,
        **kwargs
    ))

