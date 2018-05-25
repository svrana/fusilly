#!/usr/bin/env python

import unittest

from fusilly.exceptions import BuildConfigError
from fusilly.targets.command import command_target


class TestCommandTarget(unittest.TestCase):
    def setUp(self):
        pass

    def test_artifact_creation(self):
        kwargs = {'directory': 'foo/bar/baz'}
        self.assertRaisesRegexp(
            BuildConfigError,
            "command_target \w+ must contain a 'command' key",
            command_target,
            'foo_target_name',
            **kwargs
        )
