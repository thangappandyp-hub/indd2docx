from __future__ import annotations

from pathlib import Path
import tempfile

from .idml.package import IDMLPackage
from .indesign.exporter import InDesignExporter


class ConversionPipeline:
    """Top-level orchestration boundary.

    Phase 1 implements only the INDD -> IDML -> validated/extracted IDML
    boundary. DOCX rendering is deliberately not coupled to this stage.
    """

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
            package.validate()
            extracted_root = package.extract()

        # Phase 2 will parse extracted_root into the independent DocumentModel.
        # Do not manufacture a DOCX here: each pipeline boundary is tested first.
        return {
            "idml": idml_path,
            "extracted": extracted_root,
            "docx": output_path,
        }
