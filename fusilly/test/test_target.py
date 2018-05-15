#!/usr/bin/env python

import unittest
from fusilly.targets import Target


class TestTemplating(unittest.TestCase):
    def setUp(self):
        self.test_target = Target.from_dict(dict(
            func='foo',
            name='test',
            files='**/*.py',
            artifact=dict(name="foo", type="deb"),
        ))

    def test_cmdline_substition(self):
        build_spec = dict(build="npm build --env={{env}}", foo="nothing here")
        args = {'env': 'production'}
        self.test_target.make_cmdline_substitions(args, build_spec)
        self.assertEqual(
            build_spec,
            dict(build="npm build --env=production", foo="nothing here")
        )

    def test_cmdline_multi_substitution(self):
        build_spec = dict(build="npm build --env={{env}} --sha={{sha}}",
                          foo="nothing here")
        args = {'env': 'production', 'sha': '1234'}
        self.test_target.make_cmdline_substitions(args, build_spec)
        self.assertEqual(
            build_spec,
            dict(build="npm build --env=production --sha=1234",
                 foo="nothing here")
        )
