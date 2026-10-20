import json
import stat
import zipfile
from pathlib import Path
import pytest
from app.core.project import Project
from app.core.examples import adder_project, internal_adder_result
from app.utils.paths import safe_relative, confined


def rewrite(source, target, transform):
    with zipfile.ZipFile(source) as archive:
        data = {i.filename: archive.read(i.filename) for i in archive.infolist()}
    transform(data)
    with zipfile.ZipFile(target, "w") as archive:
        for name, content in data.items():
            archive.writestr(name, content)


def test_create_roundtrip_and_overwrite(tmp_path):
    p = adder_project()
    p.files["nested/helper.v"] = "module helper; endmodule"
    p.pins = {"A": "PIN_1"}
    p.artifacts.update(internal_adder_result())
    path = p.save(tmp_path / "ó prueba.pforge")
    q = Project.open(path)
    assert q == p
    with pytest.raises(FileExistsError):
        p.save(path)
    p.name = "Changed"
    p.save(path, overwrite=True)
    assert Project.open(path).name == "Changed"


def test_integrity_detects_corruption(tmp_path):
    source = adder_project().save(tmp_path / "good.pforge")
    rewrite(source, tmp_path / "bad.pforge", lambda d: d.update({"src/full_adder.v": b"tampered"}))
    with pytest.raises(ValueError, match="Integridad"):
        Project.open(tmp_path / "bad.pforge")


@pytest.mark.parametrize("name", ["../escape.v", "/tmp/a.v", "C:/a.v", "a\\b.v", "a//b", "CON.v", "LPT1", "a./b", "a ", "a:b", "./a.v", "a/../b.v"])
def test_unsafe_paths(name):
    with pytest.raises(ValueError):
        safe_relative(name)


@pytest.mark.parametrize("name", ["../escape.v", "src/../../escape.v", "C:/escape.v"])
def test_zip_slip_not_extracted(tmp_path, name):
    path = tmp_path / "bad.pforge"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(name, "attack")
    with pytest.raises(ValueError):
        Project.open(path)
    assert not (tmp_path.parent / "escape.v").exists()


def test_duplicate_case_and_symlink(tmp_path):
    p = Project(files={"A.v": "", "a.v": ""})
    with pytest.raises(ValueError, match="Colisión"):
        p.validate()
    with pytest.raises(ValueError, match="directorio"):
        Project(files={"folder":"", "folder/code.v":""}).validate()
    target = tmp_path / "link.pforge"
    info = zipfile.ZipInfo("src/link")
    info.create_system = 3
    info.external_attr = (stat.S_IFLNK | 0o777) << 16
    with zipfile.ZipFile(target, "w") as archive:
        archive.writestr(info, "../../secret")
    with pytest.raises(ValueError, match="Enlaces"):
        Project.open(target)


def test_future_schema_and_migration(tmp_path):
    source = adder_project().save(tmp_path / "original.pforge")
    for version in (0, 42):
        def change(data):
            m = json.loads(data["manifest.json"])
            m["schema_version"] = version
            if version == 0:
                del m["export_state"]
            data["manifest.json"] = json.dumps(m)
        target = tmp_path / (str(version) + ".pforge")
        rewrite(source, target, change)
        if version == 0:
            p = Project.open(target)
            assert p.metadata["migrated_from"] == 0
            assert p.manifest()["schema_version"] == 1
        else:
            with pytest.raises(ValueError, match="Versión"):
                Project.open(target)


def test_inert_import_and_confined_symlink(tmp_path):
    source = tmp_path / "program.py"
    source.write_text("raise RuntimeError('DO NOT EXECUTE')", encoding="utf-8")
    p = Project()
    p.import_file(source)
    assert "program.py" in p.files
    with pytest.raises(FileExistsError):
        p.import_file(source)
    root = tmp_path / "root"
    root.mkdir()
    try:
        (root / "link").symlink_to(tmp_path, target_is_directory=True)
    except OSError:
        pytest.skip("Creating symlinks requires permission on this Windows installation")
    with pytest.raises(ValueError):
        confined(root, "link/escape")


def test_undeclared_file_and_duplicate_json(tmp_path):
    source = adder_project().save(tmp_path / "original.pforge")
    rewrite(source, tmp_path / "extra.pforge", lambda d: d.update({"payload.py": "do not run"}))
    with pytest.raises(ValueError, match="no declarados"):
        Project.open(tmp_path / "extra.pforge")
    rewrite(source, tmp_path / "json.pforge", lambda d: d.update({"manifest.json": '{"schema_version":1,"schema_version":2}'}))
    with pytest.raises(ValueError, match="duplicada"):
        Project.open(tmp_path / "json.pforge")

