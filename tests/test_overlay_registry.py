from app.overlay_registry import install_overlay_from_local, scan_local_overlays


def test_scan_local_overlays_skips_invalid(tmp_path):
    invalid = tmp_path / "installed" / "broken"
    invalid.mkdir(parents=True)
    (invalid / "manifest.json").write_text('{"id":"broken","name":"Broken"}', encoding="utf-8")
    overlays = scan_local_overlays(tmp_path)
    assert not overlays


def test_install_overlay_from_local_validates_manifest(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "manifest.json").write_text('{"id":"good","name":"Good"}', encoding="utf-8")
    (src / "index.html").write_text("<html></html>", encoding="utf-8")
    overlay_id, error = install_overlay_from_local(src, tmp_path / "installed")
    assert error is None
    assert overlay_id == "good"


def test_install_overlay_from_local_requires_id(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "manifest.json").write_text('{"name":"MissingId"}', encoding="utf-8")
    (src / "index.html").write_text("<html></html>", encoding="utf-8")
    overlay_id, error = install_overlay_from_local(src, tmp_path / "installed")
    assert overlay_id is None
    assert error is not None
