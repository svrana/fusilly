#!/usr/bin/env python

import json
import unittest

from fusilly.exceptions import MissingTemplateValue
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
        build_spec = dict(build="npm build --env={{env}} --sha={{sha}}")
        args = {'env': 'production', 'sha': '1234'}
        self.test_target.make_cmdline_substitions(args, build_spec)
        self.assertEqual(
            build_spec,
            dict(build="npm build --env=production --sha=1234")
        )

    def test_missing_option_raises(self):
        build_spec = dict(build="npm build --env={{env}} --sha={{sha}}")
        args = {'env': 'production'}
        self.assertRaises(
            MissingTemplateValue,
            self.test_target.make_cmdline_substitions,
            args,
            build_spec
        )

    def test_json_bug(self):
        cmd="npm run prod --"
        cmd_opts = json.dumps({
            'host': '{{static_file_host}}',
            'hash': '12332',
            'cacheBust': '{{cache_bust}}',
        }).replace(' ', '')
        cmd += " --env.staticUrlInfo=" + cmd_opts
        build_spec = dict(build=cmd)
        args = {'static_file_host': 'cloudwatch.cdn.aws.com',
                'cache_bust': '14'}
        self.test_target.make_cmdline_substitions(args, build_spec)
        self.assertEqual(
            build_spec,
            dict(build='npm run prod -- --env.staticUrlInfo={"cacheBust":"14","host":"cloudwatch.cdn.aws.com","hash":"12332"}')
        )
