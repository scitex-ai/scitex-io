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
    def test_skills_root_returns_path_instance(self):
        # Arrange
        # Act
        root = _skills_root()
        # Assert
        assert isinstance(root, Path)

    def test_skills_root_points_to_existing_dir(self):
        # Arrange
        # Act
        root = _skills_root()
        # Assert
        assert root.is_dir(), f"missing bundled skills at {root}"

    def test_list_skill_files_returns_nonempty_files(self):
        # Arrange
        # Act
        files = _list_skill_files(_skills_root())
        # Assert
        assert files, "expected at least one bundled skill .md"

    def test_list_skill_files_excludes_skill_md_index(self):
        # Arrange
        # Act
        files = _list_skill_files(_skills_root())
        # Assert
        assert all(p.name != "SKILL.md" for p in files)

    def test_list_skill_files_returns_empty_for_missing_dir(self, tmp_path):
        # Arrange
        missing = tmp_path / "does-not-exist"
        # Act
        result = _list_skill_files(missing)
        # Assert
        assert result == []


class TestSkillsGroup:
    @pytest.fixture
    def no_subcommand_res(self, runner):
        return runner.invoke(skills_group, [])

    @pytest.fixture
    def help_res(self, runner):
        return runner.invoke(skills_group, ["--help"])

    def test_no_subcommand_exits_with_zero_status(self, no_subcommand_res):
        # Arrange
        # Act
        # Assert
        assert no_subcommand_res.exit_code == 0

    def test_no_subcommand_prints_usage_help_text(self, no_subcommand_res):
        # Arrange
        # Act
        # Assert
        assert "Usage:" in no_subcommand_res.output

    def test_help_flag_exits_with_zero_status(self, help_res):
        # Arrange
        # Act
        # Assert
        assert help_res.exit_code == 0

    def test_help_flag_mentions_skills_in_output(self, help_res):
        # Arrange
        # Act
        # Assert
        assert "skills" in help_res.output.lower()


class TestSkillsList:
    @pytest.fixture
    def default_res(self, runner):
        return runner.invoke(skills_group, ["list"])

    @pytest.fixture
    def json_res(self, runner):
        return runner.invoke(skills_group, ["list", "--json"])

    @pytest.fixture
    def json_payload(self, json_res):
        return json.loads(json_res.output)

    def test_default_list_exits_with_zero_status(self, default_res):
        # Arrange
        # Act
        # Assert
        assert default_res.exit_code == 0, default_res.output

    def test_default_list_mentions_known_skill_names(self, default_res):
        # Arrange
        # Act
        # Assert
        assert "installation" in default_res.output or "quick-start" in default_res.output

    def test_json_list_exits_with_zero_status(self, json_res):
        # Arrange
        # Act
        # Assert
        assert json_res.exit_code == 0, json_res.output

    def test_json_list_payload_is_list_type(self, json_payload):
        # Arrange
        # Act
        # Assert
        assert isinstance(json_payload, list)

    def test_json_list_payload_is_nonempty(self, json_payload):
        # Arrange
        # Act
        # Assert
        assert json_payload, "expected non-empty skill list"

    def test_json_list_first_entry_has_name_field(self, json_payload):
        # Arrange
        # Act
        # Assert
        assert "name" in json_payload[0]

    def test_json_list_first_entry_has_path_field(self, json_payload):
        # Arrange
        # Act
        # Assert
        assert "path" in json_payload[0]


class TestSkillsGet:
    @pytest.fixture
    def first_stem(self):
        files = _list_skill_files(_skills_root())
        return files[0].stem

    @pytest.fixture
    def pretty_res(self, runner, first_stem):
        return runner.invoke(skills_group, ["get", first_stem])

    @pytest.fixture
    def md_suffix_res(self, runner, first_stem):
        return runner.invoke(skills_group, ["get", first_stem + ".md"])

    @pytest.fixture
    def json_res(self, runner, first_stem):
        return runner.invoke(skills_group, ["get", first_stem, "--json"])

    @pytest.fixture
    def json_payload(self, json_res):
        return json.loads(json_res.output)

    @pytest.fixture
    def missing_res(self, runner):
        return runner.invoke(skills_group, ["get", "nonexistent-skill-xyz"])

    def test_get_existing_pretty_exits_with_zero_status(self, pretty_res):
        # Arrange
        # Act
        # Assert
        assert pretty_res.exit_code == 0, pretty_res.output

    def test_get_existing_pretty_has_nonempty_output(self, pretty_res):
        # Arrange
        # Act
        # Assert
        assert pretty_res.output.strip()

    def test_get_with_md_suffix_exits_with_zero_status(self, md_suffix_res):
        # Arrange
        # Act
        # Assert
        assert md_suffix_res.exit_code == 0, md_suffix_res.output

    def test_get_json_exits_with_zero_status(self, json_res):
        # Arrange
        # Act
        # Assert
        assert json_res.exit_code == 0

    def test_get_json_payload_name_matches_stem(self, json_payload, first_stem):
        # Arrange
        # Act
        # Assert
        assert json_payload["name"] == first_stem

    def test_get_json_payload_has_content_field(self, json_payload):
        # Arrange
        # Act
        # Assert
        assert json_payload["content"]

    def test_get_missing_skill_exits_nonzero(self, missing_res):
        # Arrange
        # Act
        # Assert
        assert missing_res.exit_code != 0

    def test_get_missing_skill_says_not_found(self, missing_res):
        # Arrange
        # Act
        # Assert
        assert "not found" in missing_res.output


def _set_home(env, tmp_path):
    """Set HOME inside the env-restore fixture's scope."""
    env.set("HOME", str(tmp_path))


class TestSkillsInstall:
    @pytest.fixture
    def dry_run_default_res(self, runner, tmp_path, env_save_restore):
        env_save_restore.set("HOME", str(tmp_path))
        return runner.invoke(skills_group, ["install", "--dry-run"])

    @pytest.fixture
    def dry_run_no_link_res(self, runner, tmp_path, env_save_restore):
        env_save_restore.set("HOME", str(tmp_path))
        return runner.invoke(skills_group, ["install", "--dry-run", "--no-link"])

    @pytest.fixture
    def dry_run_claude_symlink_res(self, runner, tmp_path, env_save_restore):
        env_save_restore.set("HOME", str(tmp_path))
        return runner.invoke(skills_group, ["install", "--dry-run", "--claude-symlink"])

    @pytest.fixture
    def install_symlink_dest(self, tmp_path):
        return tmp_path / "skills_dest"

    @pytest.fixture
    def install_symlink_res(self, runner, install_symlink_dest):
        return runner.invoke(skills_group, ["install", "--dest", str(install_symlink_dest)])

    @pytest.fixture
    def install_copy_res(self, runner, install_symlink_dest):
        return runner.invoke(
            skills_group, ["install", "--dest", str(install_symlink_dest), "--no-link"]
        )

    def test_dry_run_default_exits_with_zero_status(self, dry_run_default_res):
        # Arrange
        # Act
        # Assert
        assert dry_run_default_res.exit_code == 0, dry_run_default_res.output

    def test_dry_run_default_says_would_symlink(self, dry_run_default_res):
        # Arrange
        # Act
        # Assert
        assert "would symlink" in dry_run_default_res.output

    def test_dry_run_no_link_exits_with_zero_status(self, dry_run_no_link_res):
        # Arrange
        # Act
        # Assert
        assert dry_run_no_link_res.exit_code == 0

    def test_dry_run_no_link_says_would_copy(self, dry_run_no_link_res):
        # Arrange
        # Act
        # Assert
        assert "would copy" in dry_run_no_link_res.output

    def test_dry_run_claude_symlink_exits_with_zero_status(self, dry_run_claude_symlink_res):
        # Arrange
        # Act
        # Assert
        assert dry_run_claude_symlink_res.exit_code == 0

    def test_dry_run_claude_symlink_mentions_dot_claude(self, dry_run_claude_symlink_res):
        # Arrange
        # Act
        # Assert
        assert ".claude" in dry_run_claude_symlink_res.output

    def test_install_symlink_exits_with_zero_status(self, install_symlink_res):
        # Arrange
        # Act
        # Assert
        assert install_symlink_res.exit_code == 0, install_symlink_res.output

    def test_install_symlink_creates_symlink_target(self, install_symlink_res, install_symlink_dest):
        # Arrange
        target = install_symlink_dest / "scitex-io"
        # Act
        # Assert
        assert target.is_symlink()

    def test_install_symlink_target_resolves_to_skills_root(
        self, install_symlink_res, install_symlink_dest
    ):
        # Arrange
        target = install_symlink_dest / "scitex-io"
        # Act
        # Assert
        assert target.resolve() == _skills_root().resolve()

    def test_install_symlink_output_says_linked(self, install_symlink_res):
        # Arrange
        # Act
        # Assert
        assert "linked" in install_symlink_res.output

    def test_install_copy_exits_with_zero_status(self, install_copy_res):
        # Arrange
        # Act
        # Assert
        assert install_copy_res.exit_code == 0, install_copy_res.output

    def test_install_copy_creates_real_directory(self, install_copy_res, install_symlink_dest):
        # Arrange
        target = install_symlink_dest / "scitex-io"
        # Act
        # Assert
        assert target.is_dir()

    def test_install_copy_does_not_create_symlink(self, install_copy_res, install_symlink_dest):
        # Arrange
        target = install_symlink_dest / "scitex-io"
        # Act
        # Assert
        assert not target.is_symlink()

    def test_install_copy_target_contains_md_files(self, install_copy_res, install_symlink_dest):
        # Arrange
        target = install_symlink_dest / "scitex-io"
        # Act
        # Assert
        assert any(target.rglob("*.md"))

    def test_install_copy_output_says_copied(self, install_copy_res):
        # Arrange
        # Act
        # Assert
        assert "copied" in install_copy_res.output

    def test_install_rerun_replaces_existing_symlink_exit_zero(
        self, runner, install_symlink_dest
    ):
        # Arrange
        runner.invoke(skills_group, ["install", "--dest", str(install_symlink_dest)])
        # Act
        res = runner.invoke(skills_group, ["install", "--dest", str(install_symlink_dest)])
        # Assert
        assert res.exit_code == 0, res.output

    def test_install_rerun_keeps_symlink_at_target(self, runner, install_symlink_dest):
        # Arrange
        runner.invoke(skills_group, ["install", "--dest", str(install_symlink_dest)])
        # Act
        runner.invoke(skills_group, ["install", "--dest", str(install_symlink_dest)])
        # Assert
        assert (install_symlink_dest / "scitex-io").is_symlink()

    def test_install_replaces_existing_dir_exit_zero(self, runner, install_symlink_dest):
        # Arrange
        (install_symlink_dest / "scitex-io").mkdir(parents=True)
        (install_symlink_dest / "scitex-io" / "stale.md").write_text("stale")
        # Act
        res = runner.invoke(
            skills_group, ["install", "--dest", str(install_symlink_dest), "--no-link"]
        )
        # Assert
        assert res.exit_code == 0, res.output

    def test_install_replaces_existing_dir_removes_stale_files(
        self, runner, install_symlink_dest
    ):
        # Arrange
        (install_symlink_dest / "scitex-io").mkdir(parents=True)
        (install_symlink_dest / "scitex-io" / "stale.md").write_text("stale")
        # Act
        runner.invoke(
            skills_group, ["install", "--dest", str(install_symlink_dest), "--no-link"]
        )
        # Assert
        assert not (install_symlink_dest / "scitex-io" / "stale.md").exists()

    def test_install_replaces_existing_file_exit_zero(self, runner, install_symlink_dest):
        # Arrange
        install_symlink_dest.mkdir()
        target = install_symlink_dest / "scitex-io"
        target.write_text("not-a-dir")
        # Act
        res = runner.invoke(skills_group, ["install", "--dest", str(install_symlink_dest)])
        # Assert
        assert res.exit_code == 0, res.output

    def test_install_replaces_existing_file_with_symlink(self, runner, install_symlink_dest):
        # Arrange
        install_symlink_dest.mkdir()
        target = install_symlink_dest / "scitex-io"
        target.write_text("not-a-dir")
        # Act
        runner.invoke(skills_group, ["install", "--dest", str(install_symlink_dest)])
        # Assert
        assert target.is_symlink()

    def test_install_claude_symlink_exits_with_zero_status(
        self, runner, tmp_path, env_save_restore
    ):
        # Arrange
        env_save_restore.set("HOME", str(tmp_path))
        dest = tmp_path / "skills_dest"
        # Act
        res = runner.invoke(
            skills_group, ["install", "--dest", str(dest), "--claude-symlink"]
        )
        # Assert
        assert res.exit_code == 0, res.output

    def test_install_claude_symlink_creates_claude_link(
        self, runner, tmp_path, env_save_restore
    ):
        # Arrange
        env_save_restore.set("HOME", str(tmp_path))
        dest = tmp_path / "skills_dest"
        # Act
        runner.invoke(skills_group, ["install", "--dest", str(dest), "--claude-symlink"])
        # Assert
        assert (tmp_path / ".claude" / "skills" / "scitex").is_symlink()

    def test_install_claude_symlink_with_existing_dir_exits_zero(
        self, runner, tmp_path, env_save_restore
    ):
        # Arrange
        env_save_restore.set("HOME", str(tmp_path))
        claude_link = tmp_path / ".claude" / "skills" / "scitex"
        claude_link.parent.mkdir(parents=True)
        claude_link.mkdir()  # pre-existing dir, not symlink
        dest = tmp_path / "skills_dest"
        # Act
        res = runner.invoke(
            skills_group, ["install", "--dest", str(dest), "--claude-symlink"]
        )
        # Assert
        assert res.exit_code == 0

    def test_install_claude_symlink_existing_dir_emits_warning(
        self, runner, tmp_path, env_save_restore
    ):
        # Arrange
        env_save_restore.set("HOME", str(tmp_path))
        claude_link = tmp_path / ".claude" / "skills" / "scitex"
        claude_link.parent.mkdir(parents=True)
        claude_link.mkdir()
        dest = tmp_path / "skills_dest"
        # Act
        res = runner.invoke(
            skills_group, ["install", "--dest", str(dest), "--claude-symlink"]
        )
        # Assert
        assert "warning" in res.output.lower()

    def test_install_claude_symlink_keeps_existing_dir_not_symlink(
        self, runner, tmp_path, env_save_restore
    ):
        # Arrange
        env_save_restore.set("HOME", str(tmp_path))
        claude_link = tmp_path / ".claude" / "skills" / "scitex"
        claude_link.parent.mkdir(parents=True)
        claude_link.mkdir()
        dest = tmp_path / "skills_dest"
        # Act
        runner.invoke(skills_group, ["install", "--dest", str(dest), "--claude-symlink"])
        # Assert
        assert not claude_link.is_symlink()
