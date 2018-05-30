# Fusilly

Fusilly is a task runner written in Python built to support the build
steps of python programs written in a 'messy monorepo', where a move to
Bazel or Pants was not immediately feasible.

## Goals

  * Share build code across projects
  * Extensibility- Easily add custom targets in Python
  * Simplicity

## Build Files

BUILD files are python files that that define the targets used to build
our project. At start-up, Fusilly will find these BUILD files and the
targets become runnable from the command-line.

Let's take the fusilly BUILD located [here](https://github.com/svrana/fusilly/blob/master/BUILD)
as an example:

```python
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
```

This BUILD file defines four targets. Each target requires a name so that it
can be be referred to by other targets and run on the command line with the
'fusilly run' command.

Let's work through each target, starting from the bottom up.

The 'fusilly' named target is a phony target. This means that it defines no
action itself, but contains a list of dependencies that must be run. In this
case, if you run 'fusilly run fusilly' the fusilly phony target will be
executed, which will result in the the build_prep command target running first.
The build_prep command target runs 'make clean' as if you typed it on the
command line. After completion, the fusilly phony target runs the aply named
'artifact' target, which is an artifact target, meaning that it will bundle the
application into an artifact. At this time, only .deb files are supported. The
artifact target specifies all the files to include in the artifact and where to
place them in the resulting deb, along with some other
[fpm](https://github.com/jordansissel/fpm) specific options. First though, the
target named 'virtualenv' is run. The virtualenv target creates a python
virtualenv and loads the requirements specified in the requirements-based.txt
file. The resulting directory containing the virtualenv is passed to the
artifact target and included in the artifact where it's placed in
/production/fusilly/virtualenv.

### Templating

All targets may have many of their definitions changed by command line
parameters. For example, the command invoked by the Command target can be
modified at runtime. This is done by passing a key/value pair to the Command
target that is not reserved for that target.

```python
  command_target(
    name='build',
    command='build --env={{env}}',
    env='stage'
  )
```

This would allow you to run build --env=production by running `fusilly run
build --env=production` on the command line. The default value for env would be
'stage'.


## Targets

Common Paramters | description
-----------------|----------------
name | the name of the target. Used by other targets to invoke this target or by the user to run the target from the command line
deps | list of target names to run prior to running this target

All targets accept 'deps', a list of targets to run before running the target.

function name     | consumes           | produces
------------------|--------------------|--------------------
artifact_target   | list of directories to include in build | details about the artifact created |
command_target    | n/a              | n/a
phony_target      | n/a              | n/a
virtualenv_target | n/a              | n/a


### Artifact

Parameters | Description
-----------|--------
files   | a list of files or file globs to include in the build.
exclude_files | a list of files or file globs to *exclude* from the build
artifact | a dictionary with the following keys: name (name of artifact), type ('deb'), target_directory, and fpm_options.

### Command

Invoked with command_target function.

Parameters | Description
-----------|--------
command    | the command to run, i.e., make clean
directory  | the directory in which to run the command. If not specified, defaults to the same file as the BUILD file where the target is defined. Relative paths OK.

### Phony

Invoked with phony_target function.

Parameters | Description
----------|------------


### Virtualenv

Invoked with virtualenv_target function.

Parameters | Description
-----------|--------
requirements | the relative path of the requirements file that contains python dependencies in pip format
target_directory | the directory to place the virtualenv in the artifact. If a relative directory, it is appended
                  to the target_directory specified in the Artifact target.

## Custom Targets

These are targets kept outside the fusilly repository. You can keep them
anywhere in your repo.  To create them, first create a directory to house them
and create a .fusilly.toml in your project root, setting the [custom_targets]
directory to point to this directory.

For your targets to be loaded properly they must comform to the following rules:
  * The target function must have the same name as the filename (without the extension) plus '_target'
  If you want to create a foo target, create a foo.py and name your invoking function foo_target.
  * All targets must extend Fusilly.Target

Follow the existing targets in the [targets](https://github.com/svrana/fusilly/tree/master/targets/targets/) directory as examples.


## Configuration

Fusilly will parse a [toml](https://github.com/toml-lang/toml) file located in
the project root named .fusilly.toml. This is an optional file.

```toml
[build_files]
# directory elements in your project that should be scanned for BUILD files.
ignore_paths=['node_modules', 'vendor']

[custom_targets]
# directory where your custom targets are kept. Files in this directory will
# be imported by fusilly at runtime.
directory='build'
```

### Other

In a monorepo there may be many BUILD files. To locate them all, fusilly will
look through your project for each one. Fusilly must first locate your project
root. It will scan up the directory tree for a .git directory or the existence
of a .fusilly.toml file. If you do not use git, place an empty .fusilly.toml file
in your project root or submit a PR.
