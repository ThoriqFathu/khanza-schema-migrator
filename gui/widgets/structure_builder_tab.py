from PySide6.QtCore import QDateTime, QThread, Signal, Slot
from PySide6.QtWidgets import (
    QComboBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QPlainTextEdit, QPushButton, QSpinBox, QVBoxLayout, QWidget,
)

from structure_builder.database import MysqlDumpProvider
from structure_builder.models import DatabaseConfig, StructureResult
from structure_builder.service import StructureService
from gui.workers.structure_worker import StructureWorker
from .file_selector import FileSelector


class StructureBuilderTab(QWidget):
    use_existing = Signal(str)
    use_khanza = Signal(str)

    def __init__(self, parent: QWidget | None = None, service: StructureService | None = None):
        super().__init__(parent)
        self.service = service or StructureService(MysqlDumpProvider())
        self.thread: QThread | None = None
        self.worker: StructureWorker | None = None
        self.result: StructureResult | None = None
        layout = QVBoxLayout(self)
        self.form = QWidget()
        form = QFormLayout(self.form)
        self.source_type = QComboBox()
        self.source_type.addItems(["Database", "Structure SQL", "Full SQL Backup"])
        form.addRow("Source Type", self.source_type)
        self.database_group = QGroupBox("Database (read only)")
        database = QFormLayout(self.database_group)
        self.host = QLineEdit("localhost")
        self.port = QSpinBox()
        self.port.setRange(1, 65535)
        self.port.setValue(3306)
        self.database = QLineEdit()
        self.username = QLineEdit()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.dump_client = FileSelector(file_filter="All Files (*)", dialog_title="Pilih mysqldump / mariadb-dump")
        self.test_client = FileSelector(file_filter="All Files (*)", dialog_title="Pilih mysql / mariadb")
        self.dump_client.line_edit.setPlaceholderText("Otomatis dari PATH")
        self.test_client.line_edit.setPlaceholderText("Otomatis dari PATH")
        for label, widget in (
            ("Host", self.host), ("Port", self.port), ("Database", self.database),
            ("Username", self.username), ("Password", self.password),
            ("Dump executable (optional)", self.dump_client),
            ("SQL client (optional)", self.test_client),
        ):
            database.addRow(label, widget)
        self.test_button = QPushButton("Test Connection")
        self.test_button.clicked.connect(lambda: self.start("test"))
        database.addRow(self.test_button)
        form.addRow(self.database_group)
        self.input_file = FileSelector(dialog_title="Pilih SQL / Backup")
        self.input_label = QLabel("Input SQL")
        form.addRow(self.input_label, self.input_file)
        self.output_file = FileSelector(save_mode=True, dialog_title="Simpan structure.sql")
        self.output_file.set_text("structure.sql")
        form.addRow("Output File", self.output_file)
        actions = QHBoxLayout()
        self.analyze_button = QPushButton("Analyze")
        self.analyze_button.clicked.connect(lambda: self.start("analyze"))
        self.build_button = QPushButton()
        self.build_button.clicked.connect(lambda: self.start("build"))
        actions.addWidget(self.analyze_button)
        actions.addWidget(self.build_button)
        form.addRow(actions)
        layout.addWidget(self.form)
        note = QLabel(
            "Validasi dasar SQL, bukan validasi server. Migration saat ini membaca CREATE TABLE "
            "multiline dengan identifier backtick; VIEW/routine dan ALTER terpisah tidak dibandingkan."
        )
        note.setWordWrap(True)
        layout.addWidget(note)
        layout.addWidget(QLabel("Activity Log"))
        self.status = QPlainTextEdit()
        self.status.setReadOnly(True)
        self.status.setMaximumBlockCount(5000)
        self._log_password = ""
        layout.addWidget(self.status, 1)
        self.existing_button = QPushButton("Use as Existing Schema")
        self.khanza_button = QPushButton("Use as Khanza Schema")
        self.existing_button.clicked.connect(lambda: self.use_result(True))
        self.khanza_button.clicked.connect(lambda: self.use_result(False))
        handoff = QHBoxLayout()
        handoff.addWidget(self.existing_button)
        handoff.addWidget(self.khanza_button)
        layout.addLayout(handoff)
        self.source_type.currentTextChanged.connect(self.source_changed)
        self.source_changed(self.source_type.currentText())
        for field in self.form.findChildren(QLineEdit):
            field.textChanged.connect(self.invalidate_result)
        self.port.valueChanged.connect(self.invalidate_result)

    @property
    def busy(self) -> bool:
        return self.thread is not None

    @Slot()
    def invalidate_result(self) -> None:
        self.result = None
        self.existing_button.setEnabled(False)
        self.khanza_button.setEnabled(False)

    @Slot(str)
    def source_changed(self, source: str) -> None:
        self.database_group.setVisible(source == "Database")
        self.input_file.setVisible(source != "Database")
        self.input_label.setVisible(source != "Database")
        self.analyze_button.setVisible(source == "Full SQL Backup")
        self.build_button.setText({"Database": "Build Structure", "Structure SQL": "Validate", "Full SQL Backup": "Extract Structure"}[source])
        self.invalidate_result()

    def start(self, operation: str) -> None:
        if self.busy:
            return
        output = self.output_file.path()
        input_file = self.input_file.path()
        if operation == "build" and output is not None and output.exists():
            same_structure = (
                self.source_type.currentText() == "Structure SQL" and input_file is not None
                and input_file.resolve() == output.resolve()
            )
            if not same_structure and QMessageBox.question(
                self, "Output sudah ada", f"Ganti file {output}?"
            ) != QMessageBox.StandardButton.Yes:
                return
        self.invalidate_result()
        self.status.clear()
        self._log_password = self.password.text()
        self.append_activity({
            "test": "Starting connection test...",
            "analyze": "Starting backup analysis...",
            "build": "Starting structure build...",
        }.get(operation, "Starting..."))
        config = DatabaseConfig(
            self.host.text(), self.port.value(), self.database.text(),
            self.username.text(), self.password.text(),
            self.dump_client.text(), self.test_client.text(),
        )
        self.form.setEnabled(False)
        self.thread = QThread(self)
        self.worker = StructureWorker(self.service, operation, self.source_type.currentText(), input_file, output, config)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.stage.connect(self.append_activity)
        self.worker.completed.connect(self.on_completed)
        self.worker.failed.connect(self.on_failed)
        self.worker.done.connect(self.thread.quit)
        self.worker.done.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.on_thread_finished)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    @Slot(str)
    def append_activity(self, message: str) -> None:
        if self._log_password:
            message = message.replace(self._log_password, "[redacted]")
        timestamp = QDateTime.currentDateTime().toString("HH:mm:ss")
        for line in message.splitlines():
            self.status.appendPlainText(f"[{timestamp}] {line}")
        scrollbar = self.status.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    @Slot(object)
    def on_completed(self, result: object) -> None:
        if isinstance(result, StructureResult):
            self.result = result
            self.append_activity(
                f"Completed: {result.path}\n✓ SQL not empty\n✓ CREATE TABLE detected"
                f"\nTable count: {result.table_count}\nFile size: {result.size_bytes:,} bytes"
                f"\nSHA256: {result.sha256}\nRemoved statements: {result.removed_statements}"
            )
        else:
            self.append_activity(str(result))

    @Slot(str)
    def on_failed(self, message: str) -> None:
        self.invalidate_result()
        self.append_activity(f"ERROR: {message}")

    @Slot()
    def on_thread_finished(self) -> None:
        self.worker = None
        self.thread = None
        self._log_password = ""
        self.form.setEnabled(True)
        self.existing_button.setEnabled(self.result is not None)
        self.khanza_button.setEnabled(self.result is not None)

    def use_result(self, existing: bool) -> None:
        if self.busy or self.result is None:
            return
        if not self.result.path.is_file():
            self.on_failed("File hasil tidak ditemukan. Build/Validate kembali.")
            return
        signal = self.use_existing if existing else self.use_khanza
        signal.emit(str(self.result.path))
