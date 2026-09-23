"""Bounded-memory MySQL dump scanner; SQL is never executed.

Statements spill to disk after 1 MiB, including extended INSERT statements.
Quoted strings, comments, executable comments and client DELIMITER commands
are handled separately from statement terminators.
"""
import re
import shutil
from tempfile import SpooledTemporaryFile
from typing import BinaryIO, Iterator


class DumpError(ValueError):
    pass


class _Reader:
    def __init__(self, source: BinaryIO):
        self.source = source
        self.buffer = b""
        self.position = 0

    def peek(self, count: int = 1) -> bytes:
        if len(self.buffer) - self.position < count:
            self.buffer = self.buffer[self.position:] + self.source.read(65536)
            self.position = 0
        return self.buffer[self.position:self.position + count]

    def take(self, count: int = 1) -> bytes:
        result = self.peek(count)
        self.position += len(result)
        return result


def statements(source: BinaryIO) -> Iterator[tuple[BinaryIO, bytes]]:
    reader = _Reader(source)
    if reader.peek(3) == b"\xef\xbb\xbf":
        reader.take(3)
    delimiter = b";"
    quote = b""
    comment = ""
    line_start = True
    pending = bytearray()
    spool = SpooledTemporaryFile(max_size=1024 * 1024)

    def flush() -> None:
        spool.write(pending)
        pending.clear()

    try:
        while reader.peek():
            if not quote and not comment:
                if line_start and reader.peek(9).upper() == b"DELIMITER":
                    if not reader.peek(10)[9:10].isspace():
                        raise DumpError("DELIMITER tidak valid.")
                    flush()
                    spool.seek(0)
                    if significant_prefix(spool):
                        raise DumpError("DELIMITER muncul di tengah statement SQL.")
                    spool.seek(0)
                    spool.truncate()
                    reader.take(9)
                    directive = bytearray()
                    while reader.peek() and reader.peek() != b"\n":
                        directive.extend(reader.take())
                        if len(directive) > 128:
                            raise DumpError("DELIMITER terlalu panjang.")
                    delimiter = bytes(directive).strip()
                    if not delimiter or any(chr(c).isspace() for c in delimiter):
                        raise DumpError("DELIMITER tidak valid.")
                    continue
                if reader.peek(len(delimiter)) == delimiter:
                    reader.take(len(delimiter))
                    flush()
                    spool.seek(0)
                    yield spool, delimiter
                    spool.close()
                    spool = SpooledTemporaryFile(max_size=1024 * 1024)
                    line_start = False
                    continue
            char = reader.take()
            pending.extend(char)
            if comment == "line":
                if char == b"\n":
                    comment = ""
            elif comment == "block":
                if char == b"*" and reader.peek() == b"/":
                    pending.extend(reader.take())
                    comment = ""
            elif quote:
                if char == b"\\":
                    pending.extend(reader.take())
                elif char == quote:
                    if reader.peek() == quote:
                        pending.extend(reader.take())
                    else:
                        quote = b""
            elif char in (b"'", b'"', b"`"):
                quote = char
            elif char == b"#":
                comment = "line"
            elif char == b"-" and reader.peek() == b"-" and reader.peek(2)[1:2].isspace():
                pending.extend(reader.take())
                comment = "line"
            elif char == b"/" and reader.peek() == b"*":
                pending.extend(reader.take())
                comment = "block"
            if char == b"\n":
                line_start = True
            elif not char.isspace():
                line_start = False
            if len(pending) >= 65536:
                flush()
        if quote or comment == "block":
            raise DumpError("SQL terpotong: string atau comment belum ditutup.")
        flush()
        spool.seek(0)
        if significant_prefix(spool):
            raise DumpError("SQL terpotong: statement terakhir tidak memiliki terminator.")
    finally:
        spool.close()


def significant_prefix(statement: BinaryIO) -> bytes:
    """Read only a bounded prefix, skipping arbitrarily long leading comments."""
    statement.seek(0)
    reader = _Reader(statement)
    prefix = bytearray()
    while reader.peek() and len(prefix) < 8192:
        if reader.peek().isspace():
            reader.take()
            if prefix:
                prefix.extend(b" ")
        elif reader.peek(2) == b"/*":
            reader.take(2)
            executable = reader.peek() == b"!" or reader.peek(2) == b"M!"
            if executable:
                reader.take(1 if reader.peek() == b"!" else 2)
                while reader.peek() and reader.peek().isdigit():
                    reader.take()
                # Recent mariadb-dump emits a client sandbox directive, not SQL.
                if reader.peek(2) == b"\\-":
                    while reader.peek() and reader.peek(2) != b"*/":
                        reader.take()
                    reader.take(2)
                continue
            while reader.peek() and reader.peek(2) != b"*/":
                reader.take()
            reader.take(2)
        elif reader.peek(2) == b"*/":
            reader.take(2)
            prefix.extend(b" ")
        elif reader.peek() == b"#" or (
            reader.peek(2) == b"--" and reader.peek(3)[2:3].isspace()
        ):
            while reader.peek() and reader.take() != b"\n":
                pass
        else:
            prefix.extend(reader.take())
    statement.seek(0)
    return bytes(prefix).strip()


TABLE = re.compile(rb"^CREATE\s+(?:TEMPORARY\s+)?TABLE\b", re.I)
DDL = re.compile(
    rb"^(?:(?:CREATE|ALTER|DROP)\s+(?:(?:OR\s+REPLACE|TEMPORARY|UNIQUE|FULLTEXT|SPATIAL)\s+)*"
    rb"(?:TABLE|VIEW|INDEX|TRIGGER|PROCEDURE|FUNCTION|EVENT|DATABASE|SCHEMA)\b"
    rb"|CREATE\s+(?:DEFINER\s*=|ALGORITHM\s*=)|SET\b|USE\b)", re.I,
)
DATA = re.compile(rb"^(?:INSERT|REPLACE|UPDATE|DELETE|TRUNCATE|LOAD|CALL)\b", re.I)


def scan(source: BinaryIO, destination: BinaryIO | None = None, *, strict: bool = False) -> tuple[int, int]:
    tables = removed = 0
    for statement, delimiter in statements(source):
        prefix = significant_prefix(statement)
        if not prefix:
            continue
        if re.match(rb"^SET\b", prefix, re.I) and b"NO_BACKSLASH_ESCAPES" in prefix.upper():
            raise DumpError("SQL mode NO_BACKSLASH_ESCAPES belum didukung; export ulang dengan SQL mode default.")
        keep = bool(DDL.match(prefix))
        if TABLE.match(prefix):
            # Data-producing CREATE TABLE is outside schema-only dump support.
            if b"SELECT" in sql_words(statement):
                raise DumpError("CREATE TABLE ... SELECT tidak didukung; gunakan dump --no-data.")
            tables += 1
        if not keep:
            removed += 1
            if strict and DATA.match(prefix):
                raise DumpError("File mengandung statement data; gunakan Full SQL Backup.")
            if strict and not re.match(rb"^(?:(?:LOCK|UNLOCK)\s+TABLES|START\s+TRANSACTION|BEGIN|COMMIT|ROLLBACK)\b", prefix, re.I):
                raise DumpError("Statement SQL tidak didukung; gunakan Full SQL Backup.")
        elif destination is not None:
            if delimiter != b";":
                destination.write(b"DELIMITER " + delimiter + b"\n")
            shutil.copyfileobj(statement, destination, length=65536)
            destination.write(delimiter + b"\n")
            if delimiter != b";":
                destination.write(b"DELIMITER ;\n")
    return tables, removed


def sql_words(statement: BinaryIO) -> Iterator[bytes]:
    """Unquoted SQL words, with bounded buffers even for enormous definitions."""
    statement.seek(0)
    reader = _Reader(statement)
    try:
        while reader.peek():
            char = reader.take()
            if char in (b"'", b'"', b"`"):
                while reader.peek():
                    current = reader.take()
                    if current == b"\\":
                        reader.take()
                    elif current == char:
                        if reader.peek() == char:
                            reader.take()
                        else:
                            break
            elif char == b"/" and reader.peek() == b"*":
                reader.take()
                if reader.peek() == b"!" or reader.peek(2) == b"M!":
                    reader.take(1 if reader.peek() == b"!" else 2)
                    while reader.peek() and reader.peek().isdigit():
                        reader.take()
                else:
                    while reader.peek() and reader.peek(2) != b"*/":
                        reader.take()
                    reader.take(2)
            elif char == b"#" or (char == b"-" and reader.peek() == b"-" and reader.peek(2)[1:2].isspace()):
                while reader.peek() and reader.take() != b"\n":
                    pass
            elif char.isalpha() or char == b"_":
                word = bytearray(char)
                while reader.peek() and (reader.peek().isalnum() or reader.peek() in (b"_", b"$")):
                    current = reader.take()
                    if len(word) < 64:
                        word.extend(current)
                yield bytes(word).upper()
    finally:
        statement.seek(0)
