from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
)


class ConflictListWidget(QWidget):
    HEADERS = [
        "Type",
        "Table",
        "Name",
        "Decision",
    ]

    def __init__(self, parent=None):
        super().__init__(parent)

        self.conflicts = []

        # ============================================================
        # FILTER
        # ============================================================

        filter_layout = QHBoxLayout()

        type_label = QLabel("Type:")

        self.type_filter = QComboBox()

        self.type_filter.addItem(
            "All",
            None,
        )

        self.type_filter.addItem(
            "Column",
            "column",
        )

        self.type_filter.addItem(
            "Index",
            "index",
        )

        self.type_filter.addItem(
            "Primary Key",
            "primary key",
        )

        self.type_filter.addItem(
            "Foreign Key",
            "foreign key",
        )

        decision_label = QLabel(
            "Decision:"
        )

        self.decision_filter = QComboBox()

        self.decision_filter.addItem(
            "All",
            None,
        )

        self.decision_filter.addItem(
            "Keep Existing",
            "E",
        )

        self.decision_filter.addItem(
            "Use Khanza",
            "K",
        )

        self.decision_filter.addItem(
            "Skip",
            "S",
        )

        table_label = QLabel("Table:")

        self.table_filter = QLineEdit()

        self.table_filter.setPlaceholderText(
            "Filter nama tabel..."
        )

        self.clear_filter_button = QPushButton(
            "Clear"
        )

        filter_layout.addWidget(
            type_label
        )

        filter_layout.addWidget(
            self.type_filter
        )

        filter_layout.addSpacing(10)

        filter_layout.addWidget(
            decision_label
        )

        filter_layout.addWidget(
            self.decision_filter
        )

        filter_layout.addSpacing(10)

        filter_layout.addWidget(
            table_label
        )

        filter_layout.addWidget(
            self.table_filter,
            1,
        )

        filter_layout.addWidget(
            self.clear_filter_button
        )

        # ============================================================
        # RESULT COUNT
        # ============================================================

        self.result_count_label = QLabel(
            "0 conflicts"
        )

        # ============================================================
        # TABLE
        # ============================================================

        self.table = QTableWidget()

        self.table.setColumnCount(
            len(self.HEADERS)
        )

        self.table.setHorizontalHeaderLabels(
            self.HEADERS
        )

        self.table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )

        self.table.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )

        self.table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )

        self.table.verticalHeader().setVisible(
            False
        )

        header = self.table.horizontalHeader()

        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        header.setSectionResizeMode(
            1,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        header.setSectionResizeMode(
            2,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        header.setSectionResizeMode(
            3,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        # ============================================================
        # DETAIL
        # ============================================================

        self.existing_text = QPlainTextEdit()
        self.existing_text.setReadOnly(True)

        self.khanza_text = QPlainTextEdit()
        self.khanza_text.setReadOnly(True)

        existing_widget = QWidget()

        existing_layout = QVBoxLayout(
            existing_widget
        )

        existing_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        existing_layout.addWidget(
            QLabel("Existing:")
        )

        existing_layout.addWidget(
            self.existing_text
        )

        khanza_widget = QWidget()

        khanza_layout = QVBoxLayout(
            khanza_widget
        )

        khanza_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        khanza_layout.addWidget(
            QLabel("Khanza:")
        )

        khanza_layout.addWidget(
            self.khanza_text
        )

        detail_splitter = QSplitter(
            Qt.Orientation.Horizontal
        )

        detail_splitter.addWidget(
            existing_widget
        )

        detail_splitter.addWidget(
            khanza_widget
        )

        # ============================================================
        # MAIN SPLITTER
        # ============================================================

        splitter = QSplitter(
            Qt.Orientation.Vertical
        )

        splitter.addWidget(
            self.table
        )

        splitter.addWidget(
            detail_splitter
        )

        splitter.setStretchFactor(
            0,
            3,
        )

        splitter.setStretchFactor(
            1,
            2,
        )

        # ============================================================
        # MAIN LAYOUT
        # ============================================================

        layout = QVBoxLayout(self)

        layout.addLayout(
            filter_layout
        )

        layout.addWidget(
            self.result_count_label
        )

        layout.addWidget(
            splitter,
            1,
        )

        # ============================================================
        # SIGNALS
        # ============================================================

        self.type_filter.currentIndexChanged.connect(
            self.apply_filter
        )

        self.decision_filter.currentIndexChanged.connect(
            self.apply_filter
        )

        self.table_filter.textChanged.connect(
            self.apply_filter
        )

        self.clear_filter_button.clicked.connect(
            self.clear_filter
        )

        self.table.itemSelectionChanged.connect(
            self.show_selected_conflict
        )

    # ================================================================
    # DATA
    # ================================================================

    def clear(self):
        self.conflicts = []

        self.table.setRowCount(0)

        self.existing_text.clear()

        self.khanza_text.clear()

        self.result_count_label.setText(
            "0 conflicts"
        )

    def set_conflicts(self, conflicts):
        self.conflicts = list(
            conflicts
        )

        self.apply_filter()

    # ================================================================
    # FILTER
    # ================================================================

    def apply_filter(self):
        type_value = (
            self.type_filter.currentData()
        )

        decision_value = (
            self.decision_filter.currentData()
        )

        table_value = (
            self.table_filter.text()
            .strip()
            .lower()
        )

        filtered = []

        for conflict in self.conflicts:
            if (
                type_value is not None
                and conflict.object_type
                != type_value
            ):
                continue

            if (
                decision_value is not None
                and conflict.decision
                != decision_value
            ):
                continue

            if (
                table_value
                and table_value
                not in conflict.table.lower()
            ):
                continue

            filtered.append(
                conflict
            )

        self.populate_table(
            filtered
        )

        self.result_count_label.setText(
            f"{len(filtered)} dari "
            f"{len(self.conflicts)} conflicts"
        )

    def clear_filter(self):
        self.type_filter.setCurrentIndex(0)

        self.decision_filter.setCurrentIndex(0)

        self.table_filter.clear()

    # ================================================================
    # TABLE
    # ================================================================

    def populate_table(
        self,
        conflicts,
    ):
        self.table.setRowCount(0)

        self.table.setRowCount(
            len(conflicts)
        )

        for row, conflict in enumerate(
            conflicts
        ):
            type_item = QTableWidgetItem(
                conflict.object_type
            )

            type_item.setData(
                Qt.ItemDataRole.UserRole,
                conflict,
            )

            self.table.setItem(
                row,
                0,
                type_item,
            )

            self.table.setItem(
                row,
                1,
                QTableWidgetItem(
                    conflict.table
                ),
            )

            self.table.setItem(
                row,
                2,
                QTableWidgetItem(
                    conflict.name
                ),
            )

            decision_item = QTableWidgetItem(
                conflict.decision
            )

            decision_item.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            self.table.setItem(
                row,
                3,
                decision_item,
            )

        if conflicts:
            self.table.selectRow(0)
        else:
            self.existing_text.clear()
            self.khanza_text.clear()
    # ================================================================
    # DETAIL
    # ================================================================

    def show_selected_conflict(self):
        selected_rows = (
            self.table.selectionModel()
            .selectedRows()
        )

        if not selected_rows:
            self.existing_text.clear()
            self.khanza_text.clear()
            return

        row = selected_rows[0].row()

        item = self.table.item(
            row,
            0,
        )

        if item is None:
            return

        conflict = item.data(
            Qt.ItemDataRole.UserRole
        )

        if conflict is None:
            return

        self.existing_text.setPlainText(
            conflict.existing
        )

        self.khanza_text.setPlainText(
            conflict.khanza
        )