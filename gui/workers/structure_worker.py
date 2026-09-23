import logging
from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

from structure_builder.models import DatabaseConfig
from structure_builder.service import StructureService

logger = logging.getLogger(__name__)


class StructureWorker(QObject):
    completed = Signal(object)
    failed = Signal(str)
    stage = Signal(str)
    done = Signal()

    def __init__(self, service: StructureService, operation: str, source_type: str,
                 input_file: Path | None, output: Path | None, config: DatabaseConfig):
        super().__init__()
        self.service = service
        self.operation = operation
        self.source_type = source_type
        self.input_file = input_file
        self.output = output
        self.config = config

    def report(self, message: str) -> None:
        if self.config.password:
            message = message.replace(self.config.password, "[redacted]")
        self.stage.emit(message)

    @Slot()
    def run(self) -> None:
        try:
            self.report(f"Source type: {self.source_type}")
            if self.operation == "test":
                self.service.test_connection(self.config, progress=self.report)
                result = "Connected"
            elif self.operation == "analyze":
                self.report("Processing SQL backup...")
                if self.input_file is None:
                    raise ValueError("Pilih file backup.")
                tables, removed = self.service.analyze(self.input_file, progress=self.report)
                result = f"Analysis: {tables} CREATE TABLE; {removed} statement akan dibuang."
            else:
                if self.output is None:
                    raise ValueError("Tentukan Output File.")
                result = self.service.build(
                    self.source_type, self.output, input_file=self.input_file,
                    config=self.config, progress=self.report,
                )
            self.report("Completed successfully.")
            self.completed.emit(result)
        except (ValueError, OSError) as exc:
            message = str(exc)
            if self.config.password:
                message = message.replace(self.config.password, "[redacted]")
            self.failed.emit(message)
        except Exception:
            logger.error("Unexpected Structure Builder failure (details suppressed)")
            self.failed.emit("Structure Builder gagal. Periksa format SQL dan konfigurasi input.")
        finally:
            self.config = None
            self.done.emit()
