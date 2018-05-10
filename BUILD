python_artifact(
    name='fusilly',
    files=[
        '**/*.py',
    ],
    pip_requirements='requirements-base.txt',
    artifact={
        'name': 'fusilly',
        'type': 'deb',
        'target_directory': '/production/fusilly',
        'fpm_options': {
            'deb-user': 'nobody',
            'deb-group': 'nogroup',
            'maintainer': 'shaw@wish.com',
        }
    }
)
