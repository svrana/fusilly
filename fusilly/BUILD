python_artifact(
    name='fusilly',
    files=['**/*.py', '../README.md'],
    pip_requirements='requirements-base.txt',
    artifact={
        'name': 'fusilly',
        'type': 'deb',
        'fpm_options': {
            'deb-user': 'nobody',
            'deb-group': 'nogroup',
            'maintainer': 'shaw@wish.com',
        }
    }
)
