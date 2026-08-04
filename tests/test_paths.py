from types import SimpleNamespace

import pytest

from config import paths


def test_resource_path_is_rooted_in_packaged_resources():
    resource = paths.resource_path("app_icon.png")

    assert resource == paths.resource_dir() / "app_icon.png"
    assert resource.is_file()


@pytest.mark.parametrize("name", ["..\\secret.txt", "../secret.txt", "C:\\secret.txt"])
def test_resource_path_rejects_paths_outside_resource_dir(name):
    with pytest.raises(ValueError):
        paths.resource_path(name)


def test_default_export_dir_does_not_depend_on_current_directory(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    assert paths.default_export_dir() == paths.PACKAGE_ROOT / paths.EXPORT_DIR_NAME


def test_compiled_application_dir_uses_nuitka_containing_dir(monkeypatch, tmp_path):
    monkeypatch.setitem(paths.__dict__, "__compiled__", SimpleNamespace(containing_dir=str(tmp_path)))

    assert paths.application_dir() == tmp_path.resolve()


def test_relative_custom_dir_is_resolved_from_application_dir(monkeypatch, tmp_path):
    application_dir = tmp_path / "app"
    monkeypatch.setattr(paths, "application_dir", lambda: application_dir)

    assert paths.resolve_custom_dir("exports") == application_dir / "exports"


@pytest.mark.parametrize("name", ["", ".", "..", "report?.png", "CON", "name."])
def test_invalid_export_filename_is_rejected(name):
    assert paths.is_safe_filename(name) is False


def test_unique_export_path_never_overwrites_existing_file(tmp_path):
    first = tmp_path / "chart.png"
    first.touch()

    output = paths.unique_export_path(tmp_path, "chart", "PNG")

    assert output == tmp_path / "chart_1.png"
