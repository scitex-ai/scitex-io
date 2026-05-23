"""Tests for scitex_io._cli._skills: skills list/get/install."""

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from scitex_io._cli._skills import (
    _list_skill_files,
    _skills_root,
    skills_group,
)


@pytest.fixture
def runner():
    return CliRunner()


class TestHelpers:
    def test_skills_root_exists_root_is_path(self):
        # Arrange
        # Arrange
        # Act
        root = _skills_root()
        # Act
        # Assert
        # Assert
        assert isinstance(root, Path)

    def test_skills_root_exists_root_is_dir(self):
        # Arrange
        # Arrange
        # Act
        root = _skills_root()
        # Act
        # Assert
        # Assert
        assert root.is_dir(), f"missing bundled skills at {root}"


    def test_list_skill_files_nonempty_files(self):
        # Arrange
        # Arrange
        # Act
        files = _list_skill_files(_skills_root())
        # Act
        # Assert
        # Assert
        assert files, "expected at least one bundled skill .md"

    def test_list_skill_files_nonempty_all_p_name_skill_md_for_p_in_files(self):
        # Arrange
        # Arrange
        # Act
        files = _list_skill_files(_skills_root())
        # Act
        # Assert
        # Assert
        assert all(p.name != "SKILL.md" for p in files)


    def test_list_skill_files_missing_dir(self, tmp_path):
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        assert _list_skill_files(tmp_path / "does-not-exist") == []


class TestSkillsGroup:
    def test_no_subcommand_prints_help_res_exit_code_equals_n_0(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(skills_group, [])
        # Act
        # Assert
        # Assert
        assert res.exit_code == 0

    def test_no_subcommand_prints_help_usage_in_res_output(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(skills_group, [])
        # Act
        # Assert
        # Assert
        assert "Usage:" in res.output


    def test_help_res_exit_code_equals_n_0(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(skills_group, ["--help"])
        # Act
        # Assert
        # Assert
        assert res.exit_code == 0

    def test_help_skills_in_res_output_lower(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(skills_group, ["--help"])
        # Act
        # Assert
        # Assert
        assert "skills" in res.output.lower()



class TestSkillsList:
    def test_default_res_exit_code_equals_n_0(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(skills_group, ["list"])
        # Act
        # Assert
        # Assert
        assert res.exit_code == 0, res.output

    def test_default_installation_in_res_output_or_quick_start_in_res_output(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(skills_group, ["list"])
        # Act
        # Assert
        # Assert
        assert "installation" in res.output or "quick-start" in res.output


    def test_json_res_exit_code_equals_n_0(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(skills_group, ["list", "--json"])
        # Act
        # Assert
        # Assert
        assert res.exit_code == 0, res.output

    def test_json_payload_is_list(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(skills_group, ["list", "--json"])
        # Assert
        assert res.exit_code == 0, res.output
        payload = json.loads(res.output)
        # Act
        # Assert
        assert isinstance(payload, list)

    def test_json_payload_res_exit_code_equals_n_0(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(skills_group, ["list", "--json"])
        # Assert
        assert res.exit_code == 0, res.output
        payload = json.loads(res.output)
        # Act
        # Assert
        assert payload, "expected non-empty skill list"

    def test_json_name_in_payload_0(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(skills_group, ["list", "--json"])
        # Assert
        assert res.exit_code == 0, res.output
        payload = json.loads(res.output)
        # Act
        # Assert
        assert "name" in payload[0]

    def test_json_path_in_payload_0(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(skills_group, ["list", "--json"])
        # Assert
        assert res.exit_code == 0, res.output
        payload = json.loads(res.output)
        # Act
        # Assert
        assert "path" in payload[0]



class TestSkillsGet:
    def test_get_existing_pretty_res_exit_code_equals_n_0(self, runner):
        # First bundled file's stem
        # Arrange
        # Arrange
        files = _list_skill_files(_skills_root())
        stem = files[0].stem
        # Act
        res = runner.invoke(skills_group, ["get", stem])
        # Act
        # Assert
        # Assert
        assert res.exit_code == 0, res.output

    def test_get_existing_pretty_res_output_strip(self, runner):
        # First bundled file's stem
        # Arrange
        # Arrange
        files = _list_skill_files(_skills_root())
        stem = files[0].stem
        # Act
        res = runner.invoke(skills_group, ["get", stem])
        # Act
        # Assert
        # Assert
        assert res.output.strip()  # has content


    def test_get_existing_with_md_suffix(self, runner):
        # Arrange
        # Arrange
        files = _list_skill_files(_skills_root())
        stem = files[0].stem
        # Act
        # Act
        res = runner.invoke(skills_group, ["get", stem + ".md"])
        # Assert
        # Assert
        assert res.exit_code == 0, res.output

    def test_get_json_res_exit_code_equals_n_0(self, runner):
        # Arrange
        # Arrange
        files = _list_skill_files(_skills_root())
        stem = files[0].stem
        # Act
        res = runner.invoke(skills_group, ["get", stem, "--json"])
        # Act
        # Assert
        # Assert
        assert res.exit_code == 0

    def test_get_json_payload_name_stem(self, runner):
        # Arrange
        # Arrange
        files = _list_skill_files(_skills_root())
        stem = files[0].stem
        # Act
        res = runner.invoke(skills_group, ["get", stem, "--json"])
        # Assert
        assert res.exit_code == 0
        payload = json.loads(res.output)
        # Act
        # Assert
        assert payload["name"] == stem

    def test_get_json_payload_content(self, runner):
        # Arrange
        # Arrange
        files = _list_skill_files(_skills_root())
        stem = files[0].stem
        # Act
        res = runner.invoke(skills_group, ["get", stem, "--json"])
        # Assert
        assert res.exit_code == 0
        payload = json.loads(res.output)
        # Act
        # Assert
        assert payload["content"]


    def test_get_missing_skill_res_exit_code_0(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(skills_group, ["get", "nonexistent-skill-xyz"])
        # Act
        # Assert
        # Assert
        assert res.exit_code != 0

    def test_get_missing_skill_not_found_in_res_output(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(skills_group, ["get", "nonexistent-skill-xyz"])
        # Act
        # Assert
        # Assert
        assert "not found" in res.output



class TestSkillsInstall:
    def test_dry_run_default_res_exit_code_equals_n_0(self, runner, tmp_path, monkeypatch):
        # Arrange
        # Arrange
        monkeypatch.setenv("HOME", str(tmp_path))
        # Act
        res = runner.invoke(skills_group, ["install", "--dry-run"])
        # Act
        # Assert
        # Assert
        assert res.exit_code == 0, res.output

    def test_dry_run_default_would_symlink_in_res_output(self, runner, tmp_path, monkeypatch):
        # Arrange
        # Arrange
        monkeypatch.setenv("HOME", str(tmp_path))
        # Act
        res = runner.invoke(skills_group, ["install", "--dry-run"])
        # Act
        # Assert
        # Assert
        assert "would symlink" in res.output


    def test_dry_run_no_link_res_exit_code_equals_n_0(self, runner, tmp_path, monkeypatch):
        # Arrange
        # Arrange
        monkeypatch.setenv("HOME", str(tmp_path))
        # Act
        res = runner.invoke(skills_group, ["install", "--dry-run", "--no-link"])
        # Act
        # Assert
        # Assert
        assert res.exit_code == 0

    def test_dry_run_no_link_would_copy_in_res_output(self, runner, tmp_path, monkeypatch):
        # Arrange
        # Arrange
        monkeypatch.setenv("HOME", str(tmp_path))
        # Act
        res = runner.invoke(skills_group, ["install", "--dry-run", "--no-link"])
        # Act
        # Assert
        # Assert
        assert "would copy" in res.output


    def test_dry_run_claude_symlink_res_exit_code_equals_n_0(self, runner, tmp_path, monkeypatch):
        # Arrange
        # Arrange
        monkeypatch.setenv("HOME", str(tmp_path))
        # Act
        res = runner.invoke(skills_group, ["install", "--dry-run", "--claude-symlink"])
        # Act
        # Assert
        # Assert
        assert res.exit_code == 0

    def test_dry_run_claude_symlink_claude_in_res_output(self, runner, tmp_path, monkeypatch):
        # Arrange
        # Arrange
        monkeypatch.setenv("HOME", str(tmp_path))
        # Act
        res = runner.invoke(skills_group, ["install", "--dry-run", "--claude-symlink"])
        # Act
        # Assert
        # Assert
        assert ".claude" in res.output


    def test_install_symlink_res_exit_code_equals_n_0(self, runner, tmp_path):
        # Arrange
        # Arrange
        dest = tmp_path / "skills_dest"
        # Act
        res = runner.invoke(skills_group, ["install", "--dest", str(dest)])
        # Act
        # Assert
        # Assert
        assert res.exit_code == 0, res.output

    def test_install_symlink_target_is_symlink(self, runner, tmp_path):
        # Arrange
        # Arrange
        dest = tmp_path / "skills_dest"
        # Act
        res = runner.invoke(skills_group, ["install", "--dest", str(dest)])
        # Assert
        assert res.exit_code == 0, res.output
        target = dest / "scitex-io"
        # Act
        # Assert
        assert target.is_symlink()

    def test_install_symlink_target_resolve_skills_root_resolve(self, runner, tmp_path):
        # Arrange
        # Arrange
        dest = tmp_path / "skills_dest"
        # Act
        res = runner.invoke(skills_group, ["install", "--dest", str(dest)])
        # Assert
        assert res.exit_code == 0, res.output
        target = dest / "scitex-io"
        # Act
        # Assert
        assert target.resolve() == _skills_root().resolve()

    def test_install_symlink_linked_in_res_output(self, runner, tmp_path):
        # Arrange
        # Arrange
        dest = tmp_path / "skills_dest"
        # Act
        res = runner.invoke(skills_group, ["install", "--dest", str(dest)])
        # Assert
        assert res.exit_code == 0, res.output
        target = dest / "scitex-io"
        # Act
        # Assert
        assert "linked" in res.output


    def test_install_copy_res_exit_code_equals_n_0(self, runner, tmp_path):
        # Arrange
        # Arrange
        dest = tmp_path / "skills_dest"
        # Act
        res = runner.invoke(skills_group, ["install", "--dest", str(dest), "--no-link"])
        # Act
        # Assert
        # Assert
        assert res.exit_code == 0, res.output

    def test_install_copy_target_is_dir(self, runner, tmp_path):
        # Arrange
        # Arrange
        dest = tmp_path / "skills_dest"
        # Act
        res = runner.invoke(skills_group, ["install", "--dest", str(dest), "--no-link"])
        # Assert
        assert res.exit_code == 0, res.output
        target = dest / "scitex-io"
        # Act
        # Assert
        assert target.is_dir()

    def test_install_copy_not_target_is_symlink(self, runner, tmp_path):
        # Arrange
        # Arrange
        dest = tmp_path / "skills_dest"
        # Act
        res = runner.invoke(skills_group, ["install", "--dest", str(dest), "--no-link"])
        # Assert
        assert res.exit_code == 0, res.output
        target = dest / "scitex-io"
        # Act
        # Assert
        assert not target.is_symlink()

    def test_install_copy_any_target_rglob_md(self, runner, tmp_path):
        # Arrange
        # Arrange
        dest = tmp_path / "skills_dest"
        # Act
        res = runner.invoke(skills_group, ["install", "--dest", str(dest), "--no-link"])
        # Assert
        assert res.exit_code == 0, res.output
        target = dest / "scitex-io"
        # Act
        # Assert
        assert any(target.rglob("*.md"))

    def test_install_copy_copied_in_res_output(self, runner, tmp_path):
        # Arrange
        # Arrange
        dest = tmp_path / "skills_dest"
        # Act
        res = runner.invoke(skills_group, ["install", "--dest", str(dest), "--no-link"])
        # Assert
        assert res.exit_code == 0, res.output
        target = dest / "scitex-io"
        # Act
        # Assert
        assert "copied" in res.output


    def test_install_replaces_existing_symlink_res_exit_code_equals_n_0(self, runner, tmp_path):
        # Arrange
        # Arrange
        dest = tmp_path / "skills_dest"
        # First install
        runner.invoke(skills_group, ["install", "--dest", str(dest)])
        # Re-run — should unlink + recreate
        # Act
        res = runner.invoke(skills_group, ["install", "--dest", str(dest)])
        # Act
        # Assert
        # Assert
        assert res.exit_code == 0, res.output

    def test_install_replaces_existing_symlink_dest_scitex_io_is_symlink(self, runner, tmp_path):
        # Arrange
        # Arrange
        dest = tmp_path / "skills_dest"
        # First install
        runner.invoke(skills_group, ["install", "--dest", str(dest)])
        # Re-run — should unlink + recreate
        # Act
        res = runner.invoke(skills_group, ["install", "--dest", str(dest)])
        # Act
        # Assert
        # Assert
        assert (dest / "scitex-io").is_symlink()


    def test_install_replaces_existing_dir_res_exit_code_equals_n_0(self, runner, tmp_path):
        # Arrange
        # Arrange
        dest = tmp_path / "skills_dest"
        # Pre-create as plain directory
        (dest / "scitex-io").mkdir(parents=True)
        (dest / "scitex-io" / "stale.md").write_text("stale")
        # Act
        res = runner.invoke(skills_group, ["install", "--dest", str(dest), "--no-link"])
        # Act
        # Assert
        # Assert
        assert res.exit_code == 0, res.output

    def test_install_replaces_existing_dir_not_dest_scitex_io_stale_md_exists(self, runner, tmp_path):
        # Arrange
        # Arrange
        dest = tmp_path / "skills_dest"
        # Pre-create as plain directory
        (dest / "scitex-io").mkdir(parents=True)
        (dest / "scitex-io" / "stale.md").write_text("stale")
        # Act
        res = runner.invoke(skills_group, ["install", "--dest", str(dest), "--no-link"])
        # Act
        # Assert
        # Assert
        assert not (dest / "scitex-io" / "stale.md").exists()


    def test_install_replaces_existing_file_res_exit_code_equals_n_0(self, runner, tmp_path):
        # Arrange
        # Arrange
        dest = tmp_path / "skills_dest"
        dest.mkdir()
        target = dest / "scitex-io"
        target.write_text("not-a-dir")
        # Act
        res = runner.invoke(skills_group, ["install", "--dest", str(dest)])
        # Act
        # Assert
        # Assert
        assert res.exit_code == 0, res.output

    def test_install_replaces_existing_file_target_is_symlink(self, runner, tmp_path):
        # Arrange
        # Arrange
        dest = tmp_path / "skills_dest"
        dest.mkdir()
        target = dest / "scitex-io"
        target.write_text("not-a-dir")
        # Act
        res = runner.invoke(skills_group, ["install", "--dest", str(dest)])
        # Act
        # Assert
        # Assert
        assert target.is_symlink()


    def test_install_claude_symlink_creates_link_res_exit_code_equals_n_0(self, runner, tmp_path, monkeypatch):
        # Arrange
        # Arrange
        monkeypatch.setenv("HOME", str(tmp_path))
        dest = tmp_path / "skills_dest"
        # Act
        res = runner.invoke(
            skills_group,
            ["install", "--dest", str(dest), "--claude-symlink"],
        )
        # Act
        # Assert
        # Assert
        assert res.exit_code == 0, res.output

    def test_install_claude_symlink_creates_link_claude_link_is_symlink(self, runner, tmp_path, monkeypatch):
        # Arrange
        # Arrange
        monkeypatch.setenv("HOME", str(tmp_path))
        dest = tmp_path / "skills_dest"
        # Act
        res = runner.invoke(
            skills_group,
            ["install", "--dest", str(dest), "--claude-symlink"],
        )
        # Assert
        assert res.exit_code == 0, res.output
        claude_link = tmp_path / ".claude" / "skills" / "scitex"
        # Act
        # Assert
        assert claude_link.is_symlink()


    def test_install_claude_symlink_existing_nonlink_warns_res_exit_code_equals_n_0(
        self, runner, tmp_path, monkeypatch
    ):
        # Arrange
        # Arrange
        monkeypatch.setenv("HOME", str(tmp_path))
        claude_link = tmp_path / ".claude" / "skills" / "scitex"
        claude_link.parent.mkdir(parents=True)
        claude_link.mkdir()  # pre-existing dir, not symlink
        dest = tmp_path / "skills_dest"
        # Act
        res = runner.invoke(
            skills_group,
            ["install", "--dest", str(dest), "--claude-symlink"],
        )
        # Act
        # Assert
        # Assert
        assert res.exit_code == 0

    def test_install_claude_symlink_existing_nonlink_warns_warning_in_res_output_lower(
        self, runner, tmp_path, monkeypatch
    ):
        # Arrange
        # Arrange
        monkeypatch.setenv("HOME", str(tmp_path))
        claude_link = tmp_path / ".claude" / "skills" / "scitex"
        claude_link.parent.mkdir(parents=True)
        claude_link.mkdir()  # pre-existing dir, not symlink
        dest = tmp_path / "skills_dest"
        # Act
        res = runner.invoke(
            skills_group,
            ["install", "--dest", str(dest), "--claude-symlink"],
        )
        # Act
        # Assert
        # Assert
        assert "warning" in res.output.lower()

    def test_install_claude_symlink_existing_nonlink_warns_not_claude_link_is_symlink(
        self, runner, tmp_path, monkeypatch
    ):
        # Arrange
        # Arrange
        monkeypatch.setenv("HOME", str(tmp_path))
        claude_link = tmp_path / ".claude" / "skills" / "scitex"
        claude_link.parent.mkdir(parents=True)
        claude_link.mkdir()  # pre-existing dir, not symlink
        dest = tmp_path / "skills_dest"
        # Act
        res = runner.invoke(
            skills_group,
            ["install", "--dest", str(dest), "--claude-symlink"],
        )
        # Act
        # Assert
        # Assert
        assert not claude_link.is_symlink()

