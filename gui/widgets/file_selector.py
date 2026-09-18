from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QWidget,
)


class FileSelector(QWidget):
    def __init__(
        self,
        parent=None,
        *,
        dialog_title: str = "Pilih File",
        file_filter: str = "SQL Files (*.sql);;All Files (*)",
        save_mode: bool = False,
    ):
        super().__init__(parent)

        self.dialog_title = dialog_title
        self.file_filter = file_filter
        self.save_mode = save_mode

        self.line_edit = QLineEdit()

        self.browse_button = QPushButton("Browse...")

        self.browse_button.clicked.connect(
            self.browse
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(
            self.line_edit,
            1,
        )

        layout.addWidget(
            self.browse_button,
        )

    def browse(self):
        if self.save_mode:
            filename, _ = QFileDialog.getSaveFileName(
                self,
                self.dialog_title,
                self.line_edit.text(),
                self.file_filter,
            )
        else:
            filename, _ = QFileDialog.getOpenFileName(
                self,
                self.dialog_title,
                "",
                self.file_filter,
            )

        if filename:
            self.line_edit.setText(filename)

    def text(self) -> str:
        return self.line_edit.text().strip()

    def set_text(self, value: str):
        self.line_edit.setText(value)

    def path(self) -> Path | None:
        value = self.text()

        if not value:
            return None

        return Path(value)