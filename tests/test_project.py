from pathlib import Path
import indd2docx


def test_package_version():
    assert indd2docx.__version__ == "0.1.0"


def test_architecture_directories_exist():
    root = Path(__file__).parents[1]
    required = [
        "src/indd2docx/indesign",
        "src/indd2docx/idml",
        "src/indd2docx/model",
        "src/indd2docx/docx",
        "src/indd2docx/validation",
        "src/indd2docx/reporting",
    ]
    for path in required:
        assert (root / path).is_dir()
