import json
import subprocess
from pathlib import Path

import hermes_cli.banner as banner


class _FakeCompleted:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_resolve_repo_dir_prefers_imported_project_root(monkeypatch, tmp_path):
    legacy_home = tmp_path / "hermes-home"
    legacy_repo = legacy_home / "hermes-agent"
    legacy_repo.mkdir(parents=True)
    (legacy_repo / ".git").mkdir()

    project_root = tmp_path / "active-repo"
    project_root.mkdir(parents=True)
    (project_root / ".git").mkdir()

    fake_file = project_root / "hermes_cli" / "banner.py"
    fake_file.parent.mkdir(parents=True)
    fake_file.write_text("# test")

    monkeypatch.setattr(banner, "get_hermes_home", lambda: legacy_home)
    monkeypatch.setattr(banner, "__file__", str(fake_file))

    assert banner._resolve_repo_dir() == project_root.resolve()


def test_check_for_updates_cache_is_scoped_to_repo(monkeypatch, tmp_path):
    hermes_home = tmp_path / "hermes-home"
    hermes_home.mkdir()

    repo_a = tmp_path / "repo-a"
    repo_b = tmp_path / "repo-b"
    for repo in (repo_a, repo_b):
        repo.mkdir()
        (repo / ".git").mkdir()

    calls = []
    current_repo = {"path": repo_a}

    def fake_run(cmd, capture_output=False, text=False, timeout=None, cwd=None):
        cmd_str = " ".join(cmd)
        calls.append((cmd_str, cwd))
        if cmd[:3] == ["git", "fetch", "origin"]:
            return _FakeCompleted(returncode=0, stdout="", stderr="")
        if cmd[:3] == ["git", "rev-list", "--count"]:
            if Path(cwd) == repo_a:
                return _FakeCompleted(returncode=0, stdout="138\n", stderr="")
            if Path(cwd) == repo_b:
                return _FakeCompleted(returncode=0, stdout="0\n", stderr="")
        raise AssertionError(f"unexpected command: {cmd}")

    monkeypatch.setattr(banner, "get_hermes_home", lambda: hermes_home)
    monkeypatch.setattr(banner, "_resolve_repo_dir", lambda: current_repo["path"])
    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(banner.time, "time", lambda: 1000)

    assert banner.check_for_updates() == 138
    cache = json.loads((hermes_home / ".update_check").read_text())
    assert cache["repo_dir"] == str(repo_a.resolve())

    current_repo["path"] = repo_b
    assert banner.check_for_updates() == 0

    rev_list_calls = [cwd for cmd, cwd in calls if "rev-list --count HEAD..origin/main" in cmd]
    assert rev_list_calls == [str(repo_a), str(repo_b)]
