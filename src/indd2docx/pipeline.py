from __future__ import annotations

from pathlib import Path
import tempfile

from .idml.package import IDMLPackage
from .indesign.exporter import InDesignExporter


class ConversionPipeline:
    """Top-level orchestration boundary for the conversion stages."""

    def convert(self, input_path: Path, output_path: Path):
        input_path = Path(input_path).resolve()
        output_path = Path(output_path).resolve()
        suffix = input_path.suffix.lower()
        if suffix not in {".indd", ".idml"}:
            raise ValueError("Input must be .indd or .idml")

        if suffix == ".indd":
            idml_path = output_path.with_suffix(".idml")
            InDesignExporter().export(input_path, idml_path)
        else:
            idml_path = input_path

        with tempfile.TemporaryDirectory(prefix="indd2docx-") as temp_dir:
            package = IDMLPackage(idml_path, Path(temp_dir))
            members = package.validate()
            package.extract()

        # Phase 2 will parse the extracted package into the independent
        # DocumentModel. No DOCX is manufactured at this boundary.
        return {
            "idml": idml_path,
            "validated": True,
            "member_count": len(members),
            "docx": output_path,
        }
