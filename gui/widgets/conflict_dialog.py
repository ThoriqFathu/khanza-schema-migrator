from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QPlainTextEdit,
    QVBoxLayout,
)

from schema_generator.conflict import ConflictDecision


class ConflictDialog(QDialog):
    def __init__(
        self,
        parent=None,
        *,
        object_type: str,
        table: str,
        name: str,
        existing: str,
        khanza: str,
    ):
        super().__init__(parent)

        self.setWindowTitle(
            "Schema Conflict"
        )

        self.resize(900, 650)

        self._decision: ConflictDecision | None = None

        layout = QVBoxLayout(self)

        info_layout = QFormLayout()

        info_layout.addRow(
            "Type:",
            QLabel(object_type),
        )

        info_layout.addRow(
            "Table:",
            QLabel(table),
        )

        info_layout.addRow(
            "Name:",
            QLabel(name),
        )

        layout.addLayout(info_layout)

        existing_label = QLabel(
            "Existing:"
        )

        self.existing_text = QPlainTextEdit()
        self.existing_text.setPlainText(
            existing
        )
        self.existing_text.setReadOnly(True)

        layout.addWidget(existing_label)
        layout.addWidget(
            self.existing_text,
            1,
        )

        khanza_label = QLabel(
            "Khanza:"
        )

        self.khanza_text = QPlainTextEdit()
        self.khanza_text.setPlainText(
            khanza
        )
        self.khanza_text.setReadOnly(True)

        layout.addWidget(khanza_label)
        layout.addWidget(
            self.khanza_text,
            1,
        )

        self.remember_checkbox = QCheckBox(
            "Gunakan keputusan ini untuk semua "
            "conflict pada tabel ini"
        )

        layout.addWidget(
            self.remember_checkbox
        )

        buttons = QDialogButtonBox()

        self.keep_button = buttons.addButton(
            "Keep Existing",
            QDialogButtonBox.AcceptRole,
        )

        self.khanza_button = buttons.addButton(
            "Use Khanza",
            QDialogButtonBox.AcceptRole,
        )

        self.skip_button = buttons.addButton(
            "Skip",
            QDialogButtonBox.AcceptRole,
        )

        self.keep_button.clicked.connect(
            lambda: self.choose("E")
        )

        self.khanza_button.clicked.connect(
            lambda: self.choose("K")
        )

        self.skip_button.clicked.connect(
            lambda: self.choose("S")
        )

        layout.addWidget(buttons)

    def choose(self, decision: str):
        self._decision = ConflictDecision(
            decision=decision,
            remember_for_table=(
                self.remember_checkbox.isChecked()
            ),
        )

        self.accept()

    @property
    def decision(
        self,
    ) -> ConflictDecision | None:
        return self._decision