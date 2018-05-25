#!/usr/bin/env python

import unittest

from fusilly.exceptions import BuildConfigError
from fusilly.targets.artifact import artifact_target


class TestArtifactTarget(unittest.TestCase):
    opts = {
        'deb-user': 'nobody',
        'deb-group': 'nogroup',
        'maintainer': 'shaw',
    }

    def setUp(self):
        pass

    def test_artifact_creation(self):
        kwargs = dict(
            files="**/*.py",
            type="deb",
            target_directory='/foo/bar/baz',
            fpm_options=self.opts,
        )
        self.assertRaisesRegexp(
            BuildConfigError,
            "artifact_target \w+ must contain an 'artifact' dictionary",
            artifact_target,
            'foo_target_name',
            **kwargs
        )

    def test_dir_mapping_subs(self):
        artifact = dict(
            type='deb',
            target_directory='/foo/bar/baz',
            fpm_options=self.opts,
        )
        target = artifact_target('foo', files="**/*.py", type="deb",
                                 artifact=artifact)
        mappings = target._get_dir_mappings(
            dict(artifact_target_dir_mappings=['/tmp/randomtempname=virtualenv'])
        )
        self.assertEqual(
            mappings,
            ['/tmp/randomtempname/=/foo/bar/baz/virtualenv']
        )
