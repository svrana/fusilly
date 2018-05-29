#!/usr/bin/env python

from setuptools import setup, find_packages


with open('README.md') as f:
    long_description = f.read()


def get_requirements(env):
    with open('requirements-{}.txt'.format(env)) as fp:
        return [x.strip() for x in fp.read().split('\n')
                if not x.startswith('#')]


install_requires = get_requirements('base')
dev_requires = install_requires + get_requirements('dev')

version = '0.0.1'

setup(
    name='fusilly',
    version=version,
    description='A silly little build tool',
    long_description=long_description,
    url='http://github.com/contextlogic/fusilly',
    author='Shaw Vrana',
    author_email='shaw@wish.com',
    packages=find_packages('.', exclude=["*.test", "*.test.*", "test.*", "test"]),
    include_package_data=True,
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    install_requires=install_requires,
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'fusilly = fusilly.main:main',
        ],
    },
    extras_require={
        'dev': dev_requires,
    },
)
