import io
import unittest

from structure_builder.sql_dump import DumpError, scan


class DumpEdgeTests(unittest.TestCase):
    def test_mariadb_sandbox_header(self):
        sql = b"/*M!999999\\- enable the sandbox mode */\nCREATE TABLE `x` (`a` int);"
        self.assertEqual(scan(io.BytesIO(sql), strict=True), (1, 0))

    def test_select_in_enum_identifier_and_comment_is_not_data(self):
        sql = b"CREATE TABLE `select` (`x` ENUM('SELECT','a;b') COMMENT 'SELECT');"
        self.assertEqual(scan(io.BytesIO(sql), strict=True), (1, 0))

    def test_create_select_after_large_definition_rejected(self):
        sql = b"CREATE TABLE `x` (`x` int COMMENT '" + b"a" * 9000 + b"') AS SELECT 1;"
        with self.assertRaisesRegex(DumpError, "SELECT"):
            scan(io.BytesIO(sql))

    def test_unsupported_sql_mode_and_truncation(self):
        for sql in (
            b"SET SQL_MODE='NO_BACKSLASH_ESCAPES'; CREATE TABLE x (a int);",
            b"CREATE TABLE x (a int)", b"/* unfinished", b"CREATE TABLE `unfinished",
        ):
            with self.subTest(sql=sql), self.assertRaises(DumpError):
                scan(io.BytesIO(sql), strict=True)

    def test_raw_procedure_and_all_schema_objects(self):
        sql = b"""CREATE TABLE `x` (`id` int);
DELIMITER //
CREATE PROCEDURE `p`() BEGIN SELECT 'a;//'; SET @x=1; END//
DELIMITER ;
CREATE VIEW `v` AS SELECT * FROM `x`;
ALTER TABLE `x` ADD KEY `idx` (`id`);
CREATE INDEX `idx2` ON `x` (`id`);
CREATE EVENT `e` ON SCHEDULE EVERY 1 DAY DO SET @x=1;
REPLACE INTO `x` VALUES (1);
"""
        output = io.BytesIO()
        self.assertEqual(scan(io.BytesIO(sql), output), (1, 1))
        for keyword in (b"PROCEDURE", b"VIEW", b"ALTER TABLE", b"CREATE INDEX", b"EVENT"):
            self.assertIn(keyword, output.getvalue())
        self.assertNotIn(b"REPLACE INTO", output.getvalue())
        self.assertEqual(scan(io.BytesIO(output.getvalue()), strict=True), (1, 0))

    def test_transaction_wrappers_validate(self):
        sql = b"START TRANSACTION; CREATE TABLE `x` (`id` int); COMMIT;"
        self.assertEqual(scan(io.BytesIO(sql), strict=True)[0], 1)
