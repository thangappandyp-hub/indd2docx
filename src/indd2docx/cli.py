from pathlib import Path
import argparse
from .pipeline import ConversionPipeline


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="indd2docx",
        description="Convert Adobe InDesign INDD to editable DOCX through IDML.",
    )
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    ConversionPipeline().convert(args.input, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
