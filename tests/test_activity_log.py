import io
import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication

from gui.widgets.structure_builder_tab import StructureBuilderTab
from gui.workers.structure_worker import StructureWorker
from structure_builder.database import MysqlDumpProvider
from structure_builder.models import DatabaseConfig
from structure_builder.progress import ProgressReader
from structure_builder.service import StructureService


class ProgressTests(unittest.TestCase):
    def test_progress_during_build_and_unchanged_bytes(self):
        with tempfile.TemporaryDirectory() as root:
            source = Path(root) / "backup.sql"
            output = Path(root) / "structure.sql"
            source.write_bytes(b"CREATE TABLE `t` (`id` int);\n" + b"INSERT INTO `t` VALUES (1);\n" * 10000)
            events = []
            def progress(message):
                # Activity must arrive while build is still working, before publish.
                self.assertFalse(output.exists())
                events.append(message)
            with patch("structure_builder.progress.time.monotonic", return_value=0):
                result = StructureService().build("Full SQL Backup", output, input_file=source, progress=progress)
            self.assertIn("Streaming SQL dump...", events)
            self.assertIn("Skipped statements: 10000", events)
            self.assertIn("Calculating SHA256...", events)
            self.assertLess(len(events), 25)
            reference = Path(root) / "reference.sql"
            StructureService().build("Full SQL Backup", reference, input_file=source)
            self.assertEqual(output.read_bytes(), reference.read_bytes())
            self.assertEqual(result.table_count, 1)

    def test_reader_throttles_and_reports_before_eof(self):
        events = []
        with patch("structure_builder.progress.time.monotonic", side_effect=[0, 0.5, 1, 1.5, 2]):
            reader = ProgressReader(io.BytesIO(b"abcdef"), 6, events.append)
            self.assertEqual(reader.read(2), b"ab")
            self.assertEqual(events, [])
            self.assertEqual(reader.read(2), b"cd")
            self.assertEqual(events, ["Read: 4 / 6 bytes"])
            self.assertEqual(reader.read(2), b"ef")
            self.assertEqual(reader.read(2), b"")
        self.assertEqual(events[-1], "Read: 6 / 6 bytes")

    def test_database_heartbeat_and_exit_status(self):
        process = MagicMock()
        process.__enter__.return_value = process
        process.wait.side_effect = [subprocess.TimeoutExpired([], 2), 0]
        process.poll.return_value = 0
        events = []
        with tempfile.TemporaryFile() as output, patch("structure_builder.database.subprocess.Popen", return_value=process):
            output.write(b"schema")
            output.flush()
            MysqlDumpProvider()._run(["client"], output, 10, events.append, "Dump")
        self.assertEqual(events, ["Dump process started.", "Dump still running; output: 6 bytes", "Dump completed."])
        process.kill.assert_not_called()

    def test_stderr_is_not_error_or_logged(self):
        events = []
        MysqlDumpProvider()._run(
            [sys.executable, "-c", "import sys; sys.stderr.write('verbose secret-password client.cnf')"],
            subprocess.DEVNULL, 10, events.append, "Dump",
        )
        self.assertEqual(events[-1], "Dump completed.")
        self.assertNotIn("secret-password", str(events))
        self.assertNotIn("client.cnf", str(events))

    def test_credential_file_error_does_not_expose_path(self):
        events = []
        config = DatabaseConfig("host", 3306, "db", "user", "secret-password")
        original_open = os.open
        def deny_credential_file(path, *args, **kwargs):
            if str(path).endswith("client.cnf"):
                raise PermissionError("/tmp/khanza-client-private/client.cnf secret-password")
            return original_open(path, *args, **kwargs)
        with patch("structure_builder.database.shutil.which", return_value="client"), patch(
            "structure_builder.database.os.open", side_effect=deny_credential_file,
        ):
            with self.assertRaisesRegex(ValueError, "Periksa izin") as context:
                MysqlDumpProvider().test_connection(config, events.append)
        text = str(events) + str(context.exception)
        self.assertNotIn("secret-password", text)
        self.assertNotIn("client.cnf", text)
        self.assertNotIn("khanza-client-private", text)

    def test_timeout_kills_and_reaps_process(self):
        process = MagicMock()
        process.__enter__.return_value = process
        process.poll.return_value = None
        process.wait.side_effect = [subprocess.TimeoutExpired([], 1), 0]
        with patch("structure_builder.database.subprocess.Popen", return_value=process), patch("structure_builder.database.time.monotonic", side_effect=[0, 0, 2]):
            with self.assertRaisesRegex(ValueError, "timeout"):
                MysqlDumpProvider()._run(["client"], subprocess.DEVNULL, 1)
        process.kill.assert_called_once()
        self.assertEqual(process.wait.call_count, 2)


class ActivityUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def pump_until(self, predicate):
        deadline = time.monotonic() + 5
        while not predicate() and time.monotonic() < deadline:
            self.app.processEvents()
            time.sleep(0.005)
        self.assertTrue(predicate())

    def test_live_ui_before_completion_error_redaction_and_cleanup(self):
        release = threading.Event()
        class GatedService:
            def build(self, *args, progress, **kwargs):
                progress("Live progress secret-password")
                if not release.wait(5):
                    raise ValueError("Test gate timed out")
                raise ValueError("Access denied secret-password")
        tab = StructureBuilderTab(service=GatedService())
        tab.password.setText("secret-password")
        tab.output_file.set_text("")  # Set a guaranteed new path below.
        with tempfile.TemporaryDirectory() as root:
            tab.output_file.set_text(str(Path(root) / "output.sql"))
            tab.status.setPlainText("previous activity")
            tab.start("build")
            try:
                self.pump_until(lambda: "Live progress" in tab.status.toPlainText())
                text = tab.status.toPlainText()
                self.assertTrue(tab.busy)
                self.assertFalse(tab.form.isEnabled())
                self.assertNotIn("previous activity", text)
                self.assertNotIn("secret-password", text)
                self.assertIn("[redacted]", text)
                self.assertRegex(text, r"\[\d{2}:\d{2}:\d{2}\] Live progress")
                self.assertNotIn("Completed", text)
            finally:
                release.set()
                self.pump_until(lambda: not tab.busy)
            self.assertTrue(tab.form.isEnabled())
            self.assertIn("ERROR: Access denied [redacted]", tab.status.toPlainText())
            self.assertIn("Live progress", tab.status.toPlainText())
            self.assertFalse(tab.existing_button.isEnabled())
            self.assertEqual(tab.status.verticalScrollBar().value(), tab.status.verticalScrollBar().maximum())
            tab.close()

    def test_worker_forwards_analyze_and_connection_progress(self):
        class FakeService:
            def analyze(self, path, progress):
                progress("Analyze active")
                return 1, 2
            def test_connection(self, config, progress):
                progress("Connection active secret-password")
        for operation, expected in (("analyze", "Analyze active"), ("test", "Connection active [redacted]")):
            worker = StructureWorker(FakeService(), operation, "Database", Path("input.sql"), None,
                                     DatabaseConfig("host", 3306, "db", "user", "secret-password"))
            events = []
            worker.stage.connect(events.append)
            worker.completed.connect(lambda result: events.append("RESULT"))
            worker.run()
            self.assertIn(expected, events)
            self.assertLess(events.index(expected), events.index("RESULT"))
            self.assertNotIn("secret-password", str(events))
