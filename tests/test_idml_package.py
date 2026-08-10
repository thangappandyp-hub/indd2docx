from pathlib import Path
import zipfile

import pytest

from indd2docx.idml.package import IDMLPackage, IDMLPackageError


def make_idml(path: Path, include_required=True):
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as package:
        if include_required:
            package.writestr("designmap.xml", "<Document/>")
            package.writestr("META-INF/container.xml", "<container/>")
        package.writestr("Stories/Story_u1.xml", "<Story/>")


def test_valid_idml_validates_and_extracts(tmp_path):
    source = tmp_path / "sample.idml"
    make_idml(source)

    package = IDMLPackage(source, tmp_path / "work")
    members = package.validate()
    root = package.extract()

    assert "designmap.xml" in members
    assert (root / "designmap.xml").is_file()
    assert (root / "META-INF" / "container.xml").is_file()
    assert package.resolve("Stories/Story_u1.xml").is_file()


def test_non_zip_is_rejected(tmp_path):
    source = tmp_path / "bad.idml"
    source.write_text("not an IDML package", encoding="utf-8")

    with pytest.raises(IDMLPackageError):
        IDMLPackage(source, tmp_path / "work").validate()


def test_missing_required_member_is_rejected(tmp_path):
    source = tmp_path / "bad.idml"
    with zipfile.ZipFile(source, "w") as package:
        package.writestr("Stories/Story_u1.xml", "<Story/>")

    with pytest.raises(IDMLPackageError, match="missing required members"):
        IDMLPackage(source, tmp_path / "work").validate()


def test_path_traversal_is_rejected(tmp_path):
    source = tmp_path / "unsafe.idml"
    with zipfile.ZipFile(source, "w") as package:
        package.writestr("designmap.xml", "<Document/>")
        package.writestr("META-INF/container.xml", "<container/>")
        package.writestr("../outside.txt", "unsafe")

    with pytest.raises(IDMLPackageError, match="Unsafe path"):
        IDMLPackage(source, tmp_path / "work").extract()
