from pathlib import Path

from PySide6.QtCore import QThread
from PySide6.QtWidgets import (
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QTabWidget,
)

from .widgets.conflict_dialog import ConflictDialog
from .widgets.conflict_mode_dialog import (
    ConflictModeDialog,
)
from gui.widgets.conflict_list import (
    ConflictListWidget,
)

from gui.widgets.summary_widget import (
    SummaryWidget,
)
from .widgets.file_selector import FileSelector
from .workers.migration_worker import MigrationWorker
from .widgets.structure_builder_tab import StructureBuilderTab


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(
            "Khanza Schema Migrator"
        )

        self.resize(1100, 750)

        self.worker = None
        self.worker_thread = None

        self.build_ui()

    def build_ui(self):
        central = QWidget()
        self.main_tabs = QTabWidget()
        self.setCentralWidget(self.main_tabs)

        # Structure Builder di tab paling kiri
        self.structure_tab = StructureBuilderTab()
        self.main_tabs.addTab(
            self.structure_tab,
            "Structure Builder",
        )

        # Schema Migration di sebelah kanan
        self.main_tabs.addTab(
            central,
            "Schema Migration",
        )

        self.structure_tab.use_existing.connect(
            self.use_structure_as_existing
        )
        self.structure_tab.use_khanza.connect(
            self.use_structure_as_khanza
        )

        main_layout = QVBoxLayout(central)

        input_group = QGroupBox(
            "Schema Input"
        )

        input_layout = QVBoxLayout(
            input_group
        )

        # Existing
        existing_row = QHBoxLayout()

        existing_label = QLabel(
            "Existing Schema:"
        )

        self.existing_selector = FileSelector(
            dialog_title=(
                "Pilih Existing Database Schema"
            ),
        )

        existing_row.addWidget(
            existing_label
        )

        existing_row.addWidget(
            self.existing_selector,
            1,
        )

        input_layout.addLayout(
            existing_row
        )

        # Khanza
        khanza_row = QHBoxLayout()

        khanza_label = QLabel(
            "Khanza Schema:"
        )

        self.khanza_selector = FileSelector(
            dialog_title=(
                "Pilih Khanza Database Schema"
            ),
        )

        khanza_row.addWidget(
            khanza_label
        )

        khanza_row.addWidget(
            self.khanza_selector,
            1,
        )

        input_layout.addLayout(
            khanza_row
        )

        # Search
        search_row = QHBoxLayout()

        search_label = QLabel(
            "Search:"
        )

        self.search_input = QLineEdit()

        self.search_input.setPlaceholderText(
            "Contoh: lab, dokter, billing"
        )

        search_row.addWidget(
            search_label
        )

        search_row.addWidget(
            self.search_input,
            1,
        )

        input_layout.addLayout(
            search_row
        )

        # Output
        output_row = QHBoxLayout()

        output_label = QLabel(
            "Output SQL:"
        )

        self.output_selector = FileSelector(
            dialog_title=(
                "Simpan Migration SQL"
            ),
            save_mode=True,
        )

        self.output_selector.set_text(
            str(
                Path.cwd()
                / "migration.sql"
            )
        )

        output_row.addWidget(
            output_label
        )

        output_row.addWidget(
            self.output_selector,
            1,
        )

        input_layout.addLayout(
            output_row
        )

        main_layout.addWidget(
            input_group
        )

        # Action
        action_layout = QHBoxLayout()

        self.generate_button = QPushButton(
            "Generate Migration"
        )

        self.generate_button.setMinimumHeight(
            40
        )

        self.generate_button.clicked.connect(
            self.generate_migration
        )

        action_layout.addStretch()

        action_layout.addWidget(
            self.generate_button
        )

        main_layout.addLayout(
            action_layout
        )

         # Result
        self.summary_widget = SummaryWidget()

        self.conflict_list_widget = (
            ConflictListWidget()
        )

        self.log_output = QPlainTextEdit()
        self.log_output.setReadOnly(True)

        self.result_tabs = QTabWidget()

        self.result_tabs.addTab(
            self.summary_widget,
            "Summary",
        )

        self.result_tabs.addTab(
            self.conflict_list_widget,
            "Conflicts (0)",
        )

        self.result_tabs.addTab(
            self.log_output,
            "Log",
        )

        main_layout.addWidget(
            self.result_tabs,
            1,
        )

        

    def use_structure_as_existing(self, path: str) -> None:
        self.existing_selector.set_text(path)
        self.main_tabs.setCurrentIndex(0)

    def use_structure_as_khanza(self, path: str) -> None:
        self.khanza_selector.set_text(path)
        self.main_tabs.setCurrentIndex(0)

    def closeEvent(self, event) -> None:
        if self.structure_tab.busy or self.worker_thread is not None:
            QMessageBox.information(self, "Proses berjalan", "Tunggu proses selesai sebelum menutup aplikasi.")
            event.ignore()
            return
        super().closeEvent(event)

    def generate_migration(self):
        self.summary_widget.clear()
        self.conflict_list_widget.clear()

        self.result_tabs.setTabText(
            1,
            "Conflicts (0)",
        )

        self.result_tabs.setCurrentIndex(2)
        existing = (
            self.existing_selector.text()
        )

        khanza = (
            self.khanza_selector.text()
        )

        output = (
            self.output_selector.text()
        )

        search = (
            self.search_input.text()
            or None
        )

        if not existing:
            QMessageBox.warning(
                self,
                "Input Belum Lengkap",
                "Pilih file Existing Schema.",
            )
            return

        if not khanza:
            QMessageBox.warning(
                self,
                "Input Belum Lengkap",
                "Pilih file Khanza Schema.",
            )
            return

        if not output:
            QMessageBox.warning(
                self,
                "Input Belum Lengkap",
                "Tentukan file output.",
            )
            return

        mode_dialog = ConflictModeDialog(
            self
        )

        if mode_dialog.exec() != QDialog.DialogCode.Accepted:
            self.log_output.appendPlainText(
                "Migration dibatalkan."
            )
            return

        conflict_mode = mode_dialog.mode
        self.log_output.clear()

        self.log(
            "Memulai migration..."
        )

        self.log(
            f"Existing : {existing}"
        )

        self.log(
            f"Khanza   : {khanza}"
        )

        self.log(
            f"Search   : {search or '-'}"
        )

        self.log(
            f"Output   : {output}"
        )
        self.log(
            f"Conflict : {conflict_mode}"
        )

        self.generate_button.setEnabled(
            False
        )

        self.worker_thread = QThread(
            self
        )

        self.worker = MigrationWorker(
            existing_file=existing,
            khanza_file=khanza,
            output_file=output,
            search=search,
            conflict_mode=conflict_mode,
        )

        self.worker.moveToThread(
            self.worker_thread
        )

        self.worker_thread.started.connect(
            self.worker.run
        )

        self.worker.stage.connect(
            self.on_stage
        )

        self.worker.conflict_requested.connect(
            self.on_conflict_requested
        )

        self.worker.finished.connect(
            self.on_finished
        )

        self.worker.failed.connect(
            self.on_failed
        )

        self.worker.finished.connect(
            self.worker_thread.quit
        )

        self.worker.failed.connect(
            self.worker_thread.quit
        )

        self.worker_thread.finished.connect(
            self.on_thread_finished
        )

        self.worker_thread.start()

    def on_stage(
        self,
        message: str,
    ):
        self.log(message)

    def on_conflict_requested(
        self,
        object_type: str,
        table: str,
        name: str,
        existing: str,
        khanza: str,
    ):
        dialog = ConflictDialog(
            self,
            object_type=object_type,
            table=table,
            name=name,
            existing=existing,
            khanza=khanza,
        )

        dialog.exec()

        decision = dialog.decision

        if decision is None:
            decision = self.make_skip_decision()

        self.log(
            f"Conflict: "
            f"{object_type} / "
            f"{table} / "
            f"{name} "
            f"-> {decision.decision}"
        )

        if (
            decision.remember_for_table
        ):
            self.log(
                "  Keputusan diterapkan "
                "untuk semua conflict "
                "pada tabel tersebut."
            )

        self.worker.set_conflict_result(
            decision
        )

    def make_skip_decision(self):
        from schema_generator.conflict import (
            ConflictDecision,
        )

        return ConflictDecision(
            decision="S",
            remember_for_table=False,
        )

    def on_finished(self, result):
        self.summary_widget.set_result(
            result
        )

        self.conflict_list_widget.set_conflicts(
            result.plan.conflicts
        )

        self.result_tabs.setTabText(
            1,
            f"Conflicts ({len(result.plan.conflicts)})",
        )

        self.result_tabs.setCurrentIndex(0)
        plan = result.plan

        self.log("")
        self.log(
            "Migration selesai."
        )

        self.log(
            f"Existing tables : "
            f"{result.existing_table_count}"
        )

        self.log(
            f"Khanza tables   : "
            f"{result.khanza_table_count}"
        )

        self.log("")
        self.log(
            f"CREATE TABLE        : "
            f"{len(plan.create_tables)}"
        )

        self.log(
            f"DROP FOREIGN KEY    : "
            f"{len(plan.drop_foreign_keys)}"
        )

        self.log(
            f"DROP COLUMN         : "
            f"{len(plan.drop_columns)}"
        )

        self.log(
            f"ADD COLUMN          : "
            f"{len(plan.add_columns)}"
        )

        self.log(
            f"MODIFY COLUMN       : "
            f"{len(plan.modify_columns)}"
        )

        self.log(
            f"DROP INDEX          : "
            f"{len(plan.drop_indexes)}"
        )

        self.log(
            f"ADD / REPLACE INDEX : "
            f"{len(plan.add_indexes) + len(plan.replace_indexes)}"
        )

        self.log(
            f"ADD FOREIGN KEY     : "
            f"{len(plan.add_foreign_keys)}"
        )

        self.log(
            f"CONFLICTS           : "
            f"{len(plan.conflicts)}"
        )

        self.log(
            f"KEPT                : "
            f"{len(plan.kept)}"
        )

        if result.cycles:
            self.log("")
            self.log(
                "WARNING: Dependency cycle:"
            )

            for cycle in result.cycles:
                self.log(
                    " -> ".join(cycle)
                )

        self.log("")
        self.log(
            f"Output: {result.output_file}"
        )

        QMessageBox.information(
            self,
            "Migration Selesai",
            "Migration SQL berhasil dibuat.\n\n"
            f"{result.output_file}",
        )

    def on_failed(
        self,
        message: str,
    ):
        self.log("")
        self.log(
            "ERROR:"
        )

        self.log(message)

        QMessageBox.critical(
            self,
            "Migration Gagal",
            message,
        )

    def on_thread_finished(self):
        self.generate_button.setEnabled(
            True
        )

        self.worker = None
        self.worker_thread = None

    def log(self, message: str):
        self.log_output.appendPlainText(
            message
        )