from .command import Command


class GitRepo(object):
    def __init__(self, project_root):
        self.project_root = project_root
        self._head_sha = None

    def head_sha(self):
        if self._head_sha is None:
            ret, stdout = Command('git rev-parse HEAD').run(
                capture_stdout=True
            )
            if ret == 0:
                self._head_sha = stdout.strip()

        return self._head_sha

    def head_sha_short(self):
        if self._head_sha is None:
            self.head_sha()
        if self._head_sha is None:
            return None

        return self._head_sha[:12]
