#!/usr/bin/env python

import unittest

from fusilly.exceptions import BuildConfigError
from fusilly.targets.phony import phony_target


class TestPhonyTarget(unittest.TestCase):
    def setUp(self):
        pass

    def test_creation(self):
        kwargs = {}
        self.assertRaisesRegexp(
            BuildConfigError,
            "phony_target \w+ without deps does nothing",
            phony_target,
            'foo_target_name',
            **kwargs
        )
