from pathlib import Path


class ConversionPipeline:
    """Top-level orchestration boundary.

    Phase 1 intentionally exposes the pipeline contract before implementing
    individual adapters. Each stage will remain independently testable.
    """

    def convert(self, input_path: Path, output_path: Path):
        suffix = input_path.suffix.lower()
        if suffix not in {".indd", ".idml"}:
            raise ValueError("Input must be .indd or .idml")
        raise NotImplementedError(
            "Phase 1 foundation is installed. INDD/IDML conversion stages are next."
        )
