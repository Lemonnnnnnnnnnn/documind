from documind.reader.media_exporter import MediaExporter
from documind.reader.package_reader import PackageReader

from tests.conftest import SAMPLE_DOCX


def test_loads_docx_package_and_relationships():
    package = PackageReader().load(SAMPLE_DOCX)

    assert package.document_root is not None
    assert package.styles_root is not None
    assert len(package.media_files) >= 2
    assert any(target.startswith("media/") for target in package.relationships.values())


def test_exports_media_to_assets_directory(tmp_path):
    package = PackageReader().load(SAMPLE_DOCX)

    exported = MediaExporter().export(package, tmp_path, assets_dir_name="assets")

    assert len(exported) >= 2
    assert all(path.startswith("./assets/") for path in exported.values())
    assert sorted((tmp_path / "assets").iterdir())
