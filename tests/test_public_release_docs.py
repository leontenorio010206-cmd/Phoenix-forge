"""Public release: attribution and separation of third-party rights."""
from pathlib import Path

from tools.package_release import selected, ROOT


def test_public_release_has_explicit_creator_and_digital_rights():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    credits = (ROOT / "CREDITS.md").read_text(encoding="utf-8")
    legal = (ROOT / "LEGAL.md").read_text(encoding="utf-8")
    notices = (ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
    assert "Leonardo Antonio Hernández Tenorio" in credits
    assert "cocreador" in credits.lower()
    for document in (credits, legal, notices):
        assert "Digital" in document
        assert "Helmut Neemann" in document
        assert "GPLv3" in document or "GPL versión 3" in document or "GPLv3" in document
        assert "https://github.com/hneemann/Digital" in document
    assert "1.7.0" in readme
    assert "primera" in readme.lower()
    assert (ROOT / "LICENSE").read_text(encoding="utf-8").startswith("MIT License")


def test_release_source_includes_attributions_not_git_history_bundle():
    for filename in ("LICENSE", "LEGAL.md", "CREDITS.md", "THIRD_PARTY_NOTICES.md"):
        assert selected(ROOT / filename)
    assert not (ROOT / "PhoenixForge_GitHub.git.bundle").exists()


def test_publication_checklist_blocks_unreviewed_history():
    checklist = (ROOT / "docs/PUBLIC_RELEASE_CHECKLIST.md").read_text(encoding="utf-8")
    assert "historial" in checklist.lower()
    assert "bundle" in checklist
    assert "credenciales" in checklist
    assert "Settings" in checklist
