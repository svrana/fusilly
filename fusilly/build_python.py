from fusilly.main import Targets


def python_artifact(name,
                    files=None, pip_requirements=None, exclude_files=None,
                    **kwargs):
    Targets.add(dict(
        func='make build',
        name=name,
        files=files,
        pip_requirements=pip_requirements,
        exclude_files=exclude_files,
        **kwargs
    ))
