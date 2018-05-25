#!/usr/bin/env python

import json
import unittest

from fusilly.exceptions import MissingTemplateValue
from fusilly.targets import Target, Targets


class TargetTest(Target):
    TEMPLATE_ATTRS = ['command']

    def run(self, inputdict):
        return None

    @classmethod
    def create(cls, name, **kwargs):
        command = kwargs.pop('command', None)
        maintainer = kwargs.pop('maintainer', None)
        build_opts = kwargs.pop('build_opts', None)

        target = TargetTest(name, **kwargs)
        # pylint: disable=W0201
        target.maintainer = maintainer
        target.build_opts = build_opts

        return target


class TestTemplating(unittest.TestCase):
    def setUp(self):
        if 'test' in Targets:
            self.test_target = Targets.get('test')
        else:
            self.test_target = TargetTest.create(
                name='test',
                command='npm run build --maintainer={maintainer} --build_opts={build_opts}',
                maintainer='nobody@wish.com',
                build_opts='none',
                sha='12345',
                env='dev'
            )

    def test_cmdline_substition(self):
        build_spec = dict(build="npm build --env={{env}}", foo="nothing here")
        args = {'env': 'production'}
        self.test_target._make_cmdline_substitions(args, build_spec)
        self.assertEqual(
            build_spec,
            dict(build="npm build --env=production", foo="nothing here")
        )

    def test_cmdline_multi_substitution(self):
        build_spec = dict(build="npm build --env={{env}} --sha={{sha}}")
        args = {'env': 'production', 'sha': '1234'}
        self.test_target._make_cmdline_substitions(args, build_spec)
        self.assertEqual(
            build_spec,
            dict(build="npm build --env=production --sha=1234")
        )

    def test_missing_option_raises(self):
        build_spec = dict(build="npm build --env={{env}} --sha={{sha}}")
        args = {'env': 'production'}
        self.assertRaises(
            MissingTemplateValue,
            self.test_target._make_cmdline_substitions,
            args,
            build_spec
        )

    def test_json_bug(self):
        cmd = "npm run prod --"
        cmd_opts = json.dumps({
            'host': '{{static_file_host}}',
            'hash': '12332',
            'cacheBust': '{{cache_bust}}',
        }).replace(' ', '')
        cmd += " --env.staticUrlInfo=" + cmd_opts
        build_spec = dict(build=cmd)
        args = {'static_file_host': 'cloudwatch.cdn.aws.com',
                'cache_bust': '14'}
        self.test_target._make_cmdline_substitions(args, build_spec)
        self.assertEqual(
            build_spec,
            dict(build='npm run prod -- --env.staticUrlInfo={"cacheBust":"14","host":"cloudwatch.cdn.aws.com","hash":"12332"}')
        )

    def test_dict_of_dicts(self):
        build_spec = {'build': {'command': "npm build --env={{env}} --sha={{sha}}"}}
        args = {'env': 'production', 'sha': '1234'}
        self.test_target._make_cmdline_substitions(args, build_spec)
        self.assertEqual(
            build_spec,
            {'build': {'command': "npm build --env=production --sha=1234"}}
        )

    def test_attr_templating(self):
        args = {'maintainer': 'shaw@wish.com', 'build_opts': 'foobar'}
        self.test_target._templating(args, build_spec)
        self.assertEqual(
            build_spec,
            {'build': {'command': "npm build --env=production --sha=1234"}}
        )
