from __future__ import annotations

from pathlib import Path
import time

# Adobe InDesign's scripting enum value for ExportFormat.INDESIGN_MARKUP.
# The value is used only as a COM late-bound enum fallback; the source INDD is
# never inspected as a binary format.
IDML_EXPORT_FORMAT = 1768189292


class InDesignAutomationError(RuntimeError):
    """Raised when InDesign cannot perform a supported IDML export."""


class InDesignExporter:
    """Export an INDD document to IDML through Adobe InDesign COM automation."""

    def __init__(self, timeout_seconds: int = 300) -> None:
        self.timeout_seconds = timeout_seconds

    def export(self, input_path: Path, output_path: Path) -> Path:
        input_path = Path(input_path).resolve()
        output_path = Path(output_path).resolve()

        if not input_path.exists():
            raise FileNotFoundError(input_path)
        if input_path.suffix.lower() != ".indd":
            raise ValueError(f"Expected .indd input, got: {input_path}")

        try:
            import win32com.client  # type: ignore
        except ImportError as exc:
            raise InDesignAutomationError(
                "pywin32 is required for INDD -> IDML. Install it with 'pip install pywin32'."
            ) from exc

        output_path.parent.mkdir(parents=True, exist_ok=True)
        if output_path.exists():
            output_path.unlink()

        app = None
        document = None
        try:
            app = self._connect(win32com.client)
            document = app.Open(str(input_path))

            # ExportFormat.INDESIGN_MARKUP is the supported IDML export format.
            # COM wrappers differ slightly between InDesign installations, so
            # try the generated/lower-case method first and the late-bound form
            # second without introducing an alternate intermediate format.
            exported = False
            for method_name in ("Export", "export", "ExportFile", "exportFile"):
                method = getattr(document, method_name, None)
                if method is None:
                    continue
                try:
                    method(IDML_EXPORT_FORMAT, str(output_path), False)
                    exported = True
                    break
                except TypeError:
                    try:
                        method(IDML_EXPORT_FORMAT, str(output_path))
                        exported = True
                        break
                    except Exception:
                        continue
                except Exception:
                    continue

            if not exported:
                raise InDesignAutomationError(
                    "InDesign COM was connected, but no supported IDML export call succeeded."
                )

            self._wait_for_file(output_path)
            return output_path
        except InDesignAutomationError:
            raise
        except Exception as exc:
            raise InDesignAutomationError(f"InDesign IDML export failed: {exc}") from exc
        finally:
            if document is not None:
                self._close_without_saving(document)

    @staticmethod
    def _connect(client):
        # Prefer an active instance so an operator can use a specific installed
        # InDesign version. Fall back to the generic COM ProgID.
        for prog_id in ("InDesign.Application.CC.2025", "InDesign.Application.CC"):
            try:
                return client.GetActiveObject(prog_id)
            except Exception:
                pass
        for prog_id in ("InDesign.Application.CC.2025", "InDesign.Application.CC"):
            try:
                return client.Dispatch(prog_id)
            except Exception:
                pass
        raise InDesignAutomationError(
            "Adobe InDesign could not be started or attached through COM."
        )

    def _wait_for_file(self, path: Path) -> None:
        deadline = time.monotonic() + self.timeout_seconds
        last_size = -1
        stable_count = 0
        while time.monotonic() < deadline:
            if path.exists():
                size = path.stat().st_size
                if size > 0 and size == last_size:
                    stable_count += 1
                    if stable_count >= 2:
                        return
                else:
                    stable_count = 0
                last_size = size
            time.sleep(0.5)
        raise TimeoutError(f"Timed out waiting for IDML export: {path}")

    @staticmethod
    def _close_without_saving(document) -> None:
        for method_name in ("Close", "close"):
            method = getattr(document, method_name, None)
            if method is None:
                continue
            for arg in (0, False):
                try:
                    method(arg)
                    return
                except Exception:
                    pass
            try:
                method()
                return
            except Exception:
                pass
