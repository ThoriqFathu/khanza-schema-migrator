import threading

from PySide6.QtCore import QObject, Signal, Slot

from schema_generator.application.migration_service import (
    MigrationService,
)
from schema_generator.conflict import ConflictDecision


class MigrationWorker(QObject):
    finished = Signal(object)
    failed = Signal(str)

    stage = Signal(str)

    conflict_requested = Signal(
        str,
        str,
        str,
        str,
        str,
    )

    def __init__(
        self,
        existing_file: str,
        khanza_file: str,
        output_file: str,
        search: str | None = None,
        conflict_mode: str = "manual",
    ):
        super().__init__()

        self.existing_file = existing_file
        self.khanza_file = khanza_file
        self.output_file = output_file
        self.search = search

        self.conflict_mode = conflict_mode

        self._conflict_event: threading.Event | None = None
        self._conflict_result: ConflictDecision | None = None

    @Slot()
    def run(self):
        try:
            self.stage.emit(
                "Membaca Existing schema..."
            )

            service = MigrationService()

            result = service.generate(
                existing_file=self.existing_file,
                khanza_file=self.khanza_file,
                output_file=self.output_file,
                search=self.search,
                conflict_callback=self.handle_conflict,
            )

            

            self.finished.emit(result)

        except Exception as exc:
            self.failed.emit(
                f"{type(exc).__name__}: {exc}"
            )

    def handle_conflict(
        self,
        object_type: str,
        table: str,
        name: str,
        existing: str,
        khanza: str,
    ) -> ConflictDecision:

        if self.conflict_mode == "khanza_all":
            return ConflictDecision(
                decision="K",
                remember_for_table=False,
            )

        event = threading.Event()

        self._conflict_event = event
        self._conflict_result = None

        self.conflict_requested.emit(
            object_type,
            table,
            name,
            existing,
            khanza,
        )

        event.wait()

        result = self._conflict_result

        self._conflict_event = None
        self._conflict_result = None

        if result is None:
            raise RuntimeError(
                "Conflict decision tidak tersedia."
            )

        return result

    def set_conflict_result(
        self,
        result: ConflictDecision,
    ):
        self._conflict_result = result

        event = self._conflict_event

        if event is not None:
            event.set()