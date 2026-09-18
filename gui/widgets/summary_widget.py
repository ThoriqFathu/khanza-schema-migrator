from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QLabel,
    QVBoxLayout,
    QWidget,
)


class SummaryWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.existing_tables = QLabel("-")
        self.khanza_tables = QLabel("-")

        self.create_tables = QLabel("-")
        self.drop_foreign_keys = QLabel("-")
        self.drop_columns = QLabel("-")
        self.add_columns = QLabel("-")
        self.modify_columns = QLabel("-")
        self.drop_indexes = QLabel("-")
        self.add_indexes = QLabel("-")
        self.add_foreign_keys = QLabel("-")
        self.conflicts = QLabel("-")
        self.kept = QLabel("-")
        self.cycles = QLabel("-")
        self.output_file = QLabel("-")

        self.output_file.setWordWrap(True)

        layout = QVBoxLayout(self)

        input_group = QGroupBox("Schema")
        input_form = QFormLayout(input_group)

        input_form.addRow(
            "Existing tables:",
            self.existing_tables,
        )

        input_form.addRow(
            "Khanza tables:",
            self.khanza_tables,
        )

        layout.addWidget(input_group)

        operation_group = QGroupBox("Migration Operations")
        operation_form = QFormLayout(operation_group)

        operation_form.addRow(
            "CREATE TABLE:",
            self.create_tables,
        )

        operation_form.addRow(
            "DROP FOREIGN KEY:",
            self.drop_foreign_keys,
        )

        operation_form.addRow(
            "DROP COLUMN:",
            self.drop_columns,
        )

        operation_form.addRow(
            "ADD COLUMN:",
            self.add_columns,
        )

        operation_form.addRow(
            "MODIFY COLUMN:",
            self.modify_columns,
        )

        operation_form.addRow(
            "DROP INDEX:",
            self.drop_indexes,
        )

        operation_form.addRow(
            "ADD / REPLACE INDEX:",
            self.add_indexes,
        )

        operation_form.addRow(
            "ADD FOREIGN KEY:",
            self.add_foreign_keys,
        )

        operation_form.addRow(
            "CONFLICTS:",
            self.conflicts,
        )

        operation_form.addRow(
            "KEPT:",
            self.kept,
        )

        layout.addWidget(operation_group)

        result_group = QGroupBox("Result")
        result_form = QFormLayout(result_group)

        result_form.addRow(
            "Dependency cycles:",
            self.cycles,
        )

        result_form.addRow(
            "Output:",
            self.output_file,
        )

        layout.addWidget(result_group)

        layout.addStretch()

    def clear(self):
        for label in (
            self.existing_tables,
            self.khanza_tables,
            self.create_tables,
            self.drop_foreign_keys,
            self.drop_columns,
            self.add_columns,
            self.modify_columns,
            self.drop_indexes,
            self.add_indexes,
            self.add_foreign_keys,
            self.conflicts,
            self.kept,
            self.cycles,
            self.output_file,
        ):
            label.setText("-")

    def set_result(self, result):
        plan = result.plan

        self.existing_tables.setText(
            str(result.existing_table_count)
        )

        self.khanza_tables.setText(
            str(result.khanza_table_count)
        )

        self.create_tables.setText(
            str(len(plan.create_tables))
        )

        self.drop_foreign_keys.setText(
            str(len(plan.drop_foreign_keys))
        )

        self.drop_columns.setText(
            str(len(plan.drop_columns))
        )

        self.add_columns.setText(
            str(len(plan.add_columns))
        )

        self.modify_columns.setText(
            str(len(plan.modify_columns))
        )

        self.drop_indexes.setText(
            str(len(plan.drop_indexes))
        )

        self.add_indexes.setText(
            str(
                len(plan.add_indexes)
                + len(plan.replace_indexes)
            )
        )

        self.add_foreign_keys.setText(
            str(len(plan.add_foreign_keys))
        )

        self.conflicts.setText(
            str(len(plan.conflicts))
        )

        self.kept.setText(
            str(len(plan.kept))
        )

        self.cycles.setText(
            str(len(result.cycles))
        )

        self.output_file.setText(
            result.output_file
        )
