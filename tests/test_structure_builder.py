import hashlib
import io
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from schema_generator.application.migration_service import MigrationService
from schema_generator.conflict import ConflictDecision
from structure_builder.database import MysqlDumpProvider
from structure_builder.models import DatabaseConfig
from structure_builder.service import StructureService
from structure_builder.sql_dump import DumpError, scan


DDL = b"""CREATE TABLE `parent` (
  `id` int NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB;
CREATE TABLE `child` (
  `id` int NOT NULL,
  `kind` enum('a,b','semi;colon') DEFAULT 'a,b',
  KEY `parent_idx` (`id`),
  CONSTRAINT `parent_fk` FOREIGN KEY (`id`) REFERENCES `parent` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""


class StructureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "input.sql"
        self.output = self.root / "structure.sql"
        self.source.write_bytes(DDL)
        self.service = StructureService()

    def test_validate_and_copy_preserve_bytes(self):
        result = self.service.build("Structure SQL", self.output, input_file=self.source)
        self.assertEqual(self.output.read_bytes(), DDL)
        self.assertEqual(result.table_count, 2)
        self.assertEqual(result.size_bytes, len(DDL))
        self.assertEqual(result.sha256, hashlib.sha256(DDL).hexdigest())
        before = self.source.stat().st_mtime_ns
        self.service.build("Structure SQL", self.source, input_file=self.source)
        self.assertEqual(self.source.stat().st_mtime_ns, before)

    def test_invalid_inputs(self):
        for sql in (b"", b"-- CREATE TABLE fake;\n", b"SELECT 1;", b"CREATE TABLE `a` (`x` text); INSERT INTO `a` VALUES ('x');"):
            with self.subTest(sql=sql):
                self.source.write_bytes(sql)
                with self.assertRaises(DumpError):
                    self.service.validate(self.source)
        with self.assertRaises(FileNotFoundError):
            self.service.validate(self.root / "missing.sql")

    def test_extract_comments_quotes_multiline_and_replace(self):
        backup = DDL + b"""-- comment ; ' ignored
INSERT INTO `child` VALUES
(1, 'a;CREATE TABLE fake;'), (2, 'it\\'s data'), (3, 'double''quote');
/* comment ; */ REPLACE INTO `child` VALUES (4, "double;quote");
/*!40000 INSERT INTO `child` VALUES (5, 'versioned') */;
"""
        self.source.write_bytes(backup)
        result = self.service.build("Full SQL Backup", self.output, input_file=self.source)
        self.assertEqual(result.table_count, 2)
        self.assertEqual(result.removed_statements, 3)
        self.assertNotIn(b"INSERT INTO", self.output.read_bytes())
        self.assertNotIn(b"REPLACE INTO", self.output.read_bytes())

    def test_delimiter_and_routine_body_preserved(self):
        routine = b"""DELIMITER $$
/*!50003 CREATE*/ /*!50017 DEFINER=`u`@`localhost`*/ /*!50003 TRIGGER `audit`
AFTER INSERT ON `child` FOR EACH ROW BEGIN
  SET @message = 'a;$$';
  INSERT INTO `parent` VALUES (NEW.id);
END */$$
DELIMITER ;
INSERT INTO `child` VALUES (1, 'a');
"""
        self.source.write_bytes(DDL + routine)
        self.service.build("Full SQL Backup", self.output, input_file=self.source)
        output = self.output.read_bytes()
        self.assertIn(b"TRIGGER `audit`", output)
        self.assertIn(b"INSERT INTO `parent`", output)
        self.assertNotIn(b"INSERT INTO `child`", output)
        self.assertEqual(self.service.validate(self.output).table_count, 2)

    def test_large_insert_and_comment_use_bounded_reads(self):
        class BoundedReader(io.BytesIO):
            def read(self, count=-1):
                if count < 0 or count > 65536:
                    raise AssertionError("Unbounded read")
                return super().read(count)
        backup = b"/*" + b"x" * 100000 + b"*/\n" + DDL
        backup += b"INSERT INTO `child` VALUES ('" + b"x;" * 600000 + b"');"
        output = io.BytesIO()
        self.assertEqual(scan(BoundedReader(backup), output), (2, 1))
        self.assertNotIn(b"INSERT", output.getvalue())

    def test_failure_preserves_output_and_source(self):
        self.output.write_bytes(b"old output")
        self.source.write_bytes(DDL + b"INSERT INTO t VALUES ('unterminated")
        with self.assertRaises(DumpError):
            self.service.build("Full SQL Backup", self.output, input_file=self.source)
        self.assertEqual(self.output.read_bytes(), b"old output")
        self.assertFalse(list(self.root.glob(".structure-*")))
        with self.assertRaises(ValueError):
            self.service.build("Full SQL Backup", self.source, input_file=self.source)

    def test_migration_service_regression(self):
        self.service.build("Full SQL Backup", self.output, input_file=self.source)
        result = MigrationService().generate(
            str(self.source), str(self.output), str(self.root / "migration.sql"),
            conflict_callback=lambda *args: ConflictDecision("E", False),
        )
        self.assertEqual(result.existing_table_count, 2)
        self.assertEqual(result.khanza_table_count, 2)
        self.assertFalse(result.plan.create_tables)
        self.assertFalse(result.plan.conflicts)

    def test_fake_database_provider(self):
        class FakeDatabase:
            def test_connection(self, config, progress=lambda _: None):
                pass
            def dump(self, config, destination, progress=lambda _: None):
                destination.write_bytes(DDL)
        service = StructureService(FakeDatabase())
        config = DatabaseConfig("host", 3306, "db", "user", "secret")
        service.test_connection(config)
        result = service.build("Database", self.output, config=config)
        self.assertEqual(result.table_count, 2)


def fake_process(code):
    process = MagicMock()
    process.__enter__.return_value = process
    process.wait.return_value = code
    process.poll.return_value = code
    return process


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.config = DatabaseConfig("host", 3306, "db", "user", 'secret"\\\npass')

    def test_read_only_arguments_and_credential_cleanup(self):
        paths = []
        def run(args, **kwargs):
            self.assertNotIn(self.config.password, repr(args))
            path = Path(args[1].split("=", 1)[1])
            paths.append(path)
            self.assertTrue(path.exists())
            if os.name != "nt":
                self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            self.assertIn("password=", path.read_text())
            if "--no-data" in args:
                self.assertIn("--skip-lock-tables", args)
                kwargs["stdout"].write(DDL)
            else:
                self.assertIn("--execute=SELECT 1", args)
            return fake_process(0)
        with tempfile.TemporaryDirectory() as root, patch("structure_builder.database.shutil.which", return_value="client"), patch("structure_builder.database.subprocess.Popen", side_effect=run):
            provider = MysqlDumpProvider()
            provider.test_connection(self.config)
            provider.dump(self.config, Path(root) / "out.sql")
        self.assertTrue(all(not path.exists() for path in paths))
        self.assertNotIn(self.config.password, repr(self.config))

    def test_missing_client_and_failure_are_actionable(self):
        with patch("structure_builder.database.shutil.which", return_value=None):
            with self.assertRaisesRegex(ValueError, "tidak ditemukan"):
                MysqlDumpProvider().test_connection(self.config)
        with patch("structure_builder.database.shutil.which", return_value="client"), patch("structure_builder.database.subprocess.Popen", return_value=fake_process(1)):
            with self.assertRaisesRegex(ValueError, "Periksa host/port") as context:
                MysqlDumpProvider().test_connection(self.config)
            self.assertNotIn(self.config.password, str(context.exception))


if __name__ == "__main__":
    unittest.main()
