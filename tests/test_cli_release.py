"""Explicit release CLI selection and safe summaries; service integrity is separate."""

import json
import sys
from types import SimpleNamespace

import pytest

from chesterfield_twin import cli
from chesterfield_twin.domain.validation_reports import ReportIssue


def arguments(monkeypatch, tmp_path, command="build", extra=None):
    flags = ["--run-id", "chosen-run", "--import-id", "b", "--import-id", "a",
             "--import-id", "c", "--report-id", "d" * 64] if command == "build" else [
                 "--release-id", "e" * 64]
    monkeypatch.setattr(sys, "argv", ["cdt", "release", command, "--data-dir",
                                    str(tmp_path / "data"), *(flags if extra is None else extra)])


def install(monkeypatch, builder):
    import chesterfield_twin.storage.releases as releases

    monkeypatch.setattr(releases, "ReleaseBuilder", builder)
    monkeypatch.setattr(cli, "load_census_credentials", lambda *a: pytest.fail("credentials"))
    monkeypatch.setattr(cli, "acquire_acs", lambda **kw: pytest.fail("acquisition"))
    monkeypatch.setattr(cli.uvicorn, "run", lambda **kw: pytest.fail("server"))


@pytest.mark.parametrize("sealed", [True, False])
def test_build_passes_only_explicit_selection_and_summarizes(tmp_path, monkeypatch, capsys, sealed):
    arguments(monkeypatch, tmp_path)

    class Builder:
        def __init__(self, root, repository_root):
            assert root == tmp_path / "data"
            assert repository_root == cli.PROJECT_ROOT

        def build(self, run_id, import_ids, *, expected_report_id):
            assert (run_id, import_ids, expected_report_id) == (
                "chosen-run", ("b", "a", "c"), "d" * 64)
            return SimpleNamespace(sealed=sealed,
                                   manifest=SimpleNamespace(release_id="e" * 64) if sealed else None,
                                   report=SimpleNamespace(report_id="f" * 64, content=SimpleNamespace(
                                       candidate_report_id="d" * 64, synthetic=True,
                                       issues=() if sealed else (ReportIssue(
                                           code="closure_invalid", message="PRIVATE-SENTINEL"),))))

    install(monkeypatch, Builder)
    assert cli.main() == (0 if sealed else 1)
    output = capsys.readouterr()
    result = json.loads(output.out)
    assert result["sealed"] is sealed
    assert result["active_pointer_changed"] is False
    assert result["synthetic"] is True
    assert result["issue_codes"] == ([] if sealed else ["closure_invalid"])
    assert "PRIVATE-SENTINEL" not in str(output)
    assert not (tmp_path / "data").exists()


def test_verify_explicitly_checks_current_dependencies(tmp_path, monkeypatch, capsys):
    arguments(monkeypatch, tmp_path, "verify")

    class Builder:
        def __init__(self, root, repository_root):
            pass

        def read_release(self, release_id, *, verify_current):
            assert release_id == "e" * 64 and verify_current is True
            return SimpleNamespace(release_id=release_id, content=SimpleNamespace(
                synthetic=False, selection=SimpleNamespace(version_ids=tuple(range(303)))))

    install(monkeypatch, Builder)
    assert cli.main() == 0
    result = json.loads(capsys.readouterr().out)
    assert result["current_dependencies_verified"] is True
    assert result["version_count"] == 303 and result["active_pointer_changed"] is False


@pytest.mark.parametrize("failure", [ValueError, OSError, RuntimeError, KeyboardInterrupt])
def test_errors_are_sanitized_and_do_not_initialize(tmp_path, monkeypatch, capsys, failure):
    arguments(monkeypatch, tmp_path)

    class Builder:
        def __init__(self, *args):
            raise failure("PRIVATE-SENTINEL")

    install(monkeypatch, Builder)
    assert cli.main() == (130 if failure is KeyboardInterrupt else 1)
    output = capsys.readouterr()
    assert "PRIVATE-SENTINEL" not in str(output)
    assert "activation" in output.err
    assert not (tmp_path / "data").exists()


@pytest.mark.parametrize("missing", ["--data-dir", "--run-id", "--import-id", "--report-id"])
def test_build_requires_each_pin(tmp_path, monkeypatch, capsys, missing):
    flags = {"--data-dir": str(tmp_path), "--run-id": "run", "--import-id": "id",
             "--report-id": "f" * 64}
    del flags[missing]
    monkeypatch.setattr(sys, "argv", ["cdt", "release", "build",
                                    *(s for pair in flags.items() for s in pair)])
    with pytest.raises(SystemExit) as error:
        cli.main()
    assert error.value.code == 2


def test_activation_rejects_unpinned_positional_arguments(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["cdt", "release", "activate", "PRIVATE-SENTINEL"])
    with pytest.raises(SystemExit) as error:
        cli.main()
    assert error.value.code == 2
    assert "PRIVATE-SENTINEL" not in str(capsys.readouterr())


def test_activation_uses_only_explicit_service_without_build_or_credentials(
    tmp_path, monkeypatch, capsys,
):
    from chesterfield_twin.domain.application import ActivationResult
    from chesterfield_twin.storage import application

    arguments(monkeypatch, tmp_path, "activate")
    install(monkeypatch, lambda *a: pytest.fail("build or verify service"))

    class Service:
        def __init__(self, root, repository_root):
            assert root == tmp_path / "data" and repository_root == cli.PROJECT_ROOT

        def activate(self, release_id):
            assert release_id == "e" * 64
            return ActivationResult(
                release_id=release_id, active_release_id=release_id,
                previous_release_id=None, changed=True, synthetic=False,
            )

    monkeypatch.setattr(application, "ReleaseApplication", Service)
    assert cli.main() == 0
    result = json.loads(capsys.readouterr().out)
    assert result["active_release_id"] == "e" * 64
    assert result["changed"] and result["current_dependencies_verified"]
    assert result["synthetic"] is False
    assert not (tmp_path / "data").exists()


@pytest.mark.parametrize("failure", [ValueError, OSError, RuntimeError, KeyboardInterrupt])
def test_activation_failure_never_prints_success_or_private_exception(
    tmp_path, monkeypatch, capsys, failure,
):
    from chesterfield_twin.storage import application

    arguments(monkeypatch, tmp_path, "activate")

    class Service:
        def __init__(self, *args):
            pass

        def activate(self, release_id):
            raise failure("PRIVATE-SENTINEL")

    monkeypatch.setattr(application, "ReleaseApplication", Service)
    assert cli.main() == (130 if failure is KeyboardInterrupt else 1)
    output = capsys.readouterr()
    assert not output.out and "PRIVATE-SENTINEL" not in output.err
    assert "active pointer" in output.err
    assert "No activation was requested" not in output.err


@pytest.mark.parametrize("missing", ["--data-dir", "--release-id"])
def test_activation_requires_root_and_release(monkeypatch, tmp_path, missing):
    flags = {"--data-dir": str(tmp_path), "--release-id": "e" * 64}
    del flags[missing]
    monkeypatch.setattr(sys, "argv", ["cdt", "release", "activate",
                                    *(s for pair in flags.items() for s in pair)])
    with pytest.raises(SystemExit) as error:
        cli.main()
    assert error.value.code == 2
