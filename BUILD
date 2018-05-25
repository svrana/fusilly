virtualenv_target(
    name='virtualenv',
    requirements='requirements-base.txt',
    target_directory='virtualenv',
)

artifact_target(
    name='artifact',

    files=[
        '**/*.py',
    ],
    exclude_files=[
        '**/test/**',
    ],

    artifact={
        'name': 'fusilly',
        'type': 'deb',
        'target_directory': '/production/fusilly',
        'fpm_options': {
            'deb-user': 'nobody',
            'deb-group': 'nogroup',
            'maintainer': 'shaw@wish.com',
        }
    },

    deps=[
        'virtualenv',
    ]
)

command_target(
    name='build_prep',
    command='make clean'
)

phony_target(
    name='fusilly',
    deps = [
        'build_prep',
        'artifact',
    ]
)
