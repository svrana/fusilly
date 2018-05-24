virtualenv_target(
    name='fusilly_virtualenv',
    requirements='requirements-base.txt',
    target_directory_name='virtualenv',
)

artifact_target(
    name='fusilly',
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
        'fusilly_virtualenv',
    ]
)
