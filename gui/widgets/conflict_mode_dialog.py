from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QRadioButton,
    QVBoxLayout,
)


class ConflictModeDialog(QDialog):
    MODE_MANUAL = "manual"
    MODE_KHANZA_ALL = "khanza_all"

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle(
            "Conflict Resolution"
        )

        self.resize(500, 280)

        self._mode = None

        layout = QVBoxLayout(self)

        title = QLabel(
            "Bagaimana conflict schema akan ditangani?"
        )

        layout.addWidget(title)

        layout.addSpacing(10)

        self.manual_radio = QRadioButton(
            "Manual Decision"
        )

        self.manual_radio.setToolTip(
            "Tampilkan dialog untuk setiap conflict "
            "agar keputusan dapat ditentukan secara manual."
        )

        self.manual_radio.setChecked(True)

        layout.addWidget(
            self.manual_radio
        )

        manual_description = QLabel(
            "Tampilkan dialog untuk setiap conflict."
        )

        manual_description.setWordWrap(True)

        layout.addWidget(
            manual_description
        )

        layout.addSpacing(10)

        self.khanza_all_radio = QRadioButton(
            "Use Khanza for All"
        )

        self.khanza_all_radio.setToolTip(
            "Semua conflict otomatis menggunakan "
            "definisi dari Khanza."
        )

        layout.addWidget(
            self.khanza_all_radio
        )

        khanza_description = QLabel(
            "Semua conflict otomatis menggunakan "
            "definisi dari Khanza."
        )

        khanza_description.setWordWrap(True)

        layout.addWidget(
            khanza_description
        )

        layout.addStretch()

        buttons = QDialogButtonBox(
            QDialogButtonBox.Cancel
            | QDialogButtonBox.Ok
        )

        buttons.accepted.connect(
            self.start
        )

        buttons.rejected.connect(
            self.reject
        )

        layout.addWidget(buttons)

    def start(self):
        if self.khanza_all_radio.isChecked():
            self._mode = self.MODE_KHANZA_ALL
        else:
            self._mode = self.MODE_MANUAL

        self.accept()

    @property
    def mode(self) -> str | None:
        return self._mode