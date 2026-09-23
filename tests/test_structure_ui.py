import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from gui.main_window import MainWindow


class StructureUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_worker_and_both_handoffs(self):
        with tempfile.TemporaryDirectory() as root:
            source = Path(root) / "input.sql"
            output = Path(root) / "output.sql"
            source.write_text("CREATE TABLE `a` (\n `id` int\n) ENGINE=InnoDB;\n")
            window = MainWindow()
            tab = window.structure_tab
            self.assertEqual(window.main_tabs.count(), 2)
            tab.source_type.setCurrentText("Full SQL Backup")
            tab.input_file.set_text(str(source))
            tab.output_file.set_text(str(output))
            tab.start("build")
            self.assertTrue(tab.busy)
            self.assertFalse(tab.form.isEnabled())
            deadline = time.monotonic() + 10
            while tab.busy and time.monotonic() < deadline:
                self.app.processEvents()
                time.sleep(0.005)
            self.assertFalse(tab.busy)
            self.assertIsNotNone(tab.result, tab.status.toPlainText())
            with patch.object(window, "generate_migration") as generate:
                window.main_tabs.setCurrentIndex(1)
                tab.existing_button.click()
                self.assertEqual(window.existing_selector.text(), str(output))
                self.assertEqual(window.main_tabs.currentIndex(), 0)
                window.main_tabs.setCurrentIndex(1)
                tab.khanza_button.click()
                self.assertEqual(window.khanza_selector.text(), str(output))
                self.assertEqual(window.main_tabs.currentIndex(), 0)
                generate.assert_not_called()
                self.assertIsNone(window.worker_thread)
            tab.input_file.set_text("changed.sql")
            self.assertFalse(tab.existing_button.isEnabled())
            window.close()

    def test_worker_error_is_reported(self):
        window = MainWindow()
        tab = window.structure_tab
        tab.source_type.setCurrentText("Full SQL Backup")
        tab.start("analyze")
        deadline = time.monotonic() + 10
        while tab.busy and time.monotonic() < deadline:
            self.app.processEvents()
            time.sleep(0.005)
        self.assertFalse(tab.busy)
        self.assertIn("ERROR:", tab.status.toPlainText())
        self.assertFalse(tab.existing_button.isEnabled())
        window.close()
