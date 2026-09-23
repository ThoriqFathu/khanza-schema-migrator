import hashlib
import logging
import os
import shutil
import tempfile
from pathlib import Path

from .models import DatabaseConfig, DatabaseProvider, StructureResult
from .sql_dump import DumpError, scan
from .progress import Progress, ProgressReader, ignore_progress

logger = logging.getLogger(__name__)


class StructureService:
    def __init__(self, database: DatabaseProvider | None = None):
        self.database = database

    def validate(self, path: Path, progress: Progress = ignore_progress) -> StructureResult:
        path = path.resolve()
        progress("Opening structure SQL...")
        progress("Validating SQL...")
        with path.open("rb") as source:
            tables, _ = scan(ProgressReader(source, os.fstat(source.fileno()).st_size, progress), strict=True)
        progress(f"Tables detected: {tables}")
        if not tables:
            raise DumpError("No CREATE TABLE statement found. Pilih file schema yang tidak kosong.")
        progress("Calculating SHA256...")
        digest = hashlib.sha256()
        with path.open("rb") as source:
            reader = ProgressReader(source, os.fstat(source.fileno()).st_size, progress, "Hashed")
            for chunk in iter(lambda: reader.read(1024 * 1024), b""):
                digest.update(chunk)
        progress("Validation completed.")
        return StructureResult(path, tables, path.stat().st_size, digest.hexdigest())

    def analyze(self, path: Path, progress: Progress = ignore_progress) -> tuple[int, int]:
        progress("Opening backup SQL...")
        with path.open("rb") as source:
            size = os.fstat(source.fileno()).st_size
            progress(f"File size: {size:,} bytes")
            progress("Streaming SQL dump...")
            tables, removed = scan(ProgressReader(source, size, progress))
        progress(f"Tables detected: {tables}")
        progress(f"Statements to skip: {removed}")
        return tables, removed

    def test_connection(self, config: DatabaseConfig, progress: Progress = ignore_progress) -> None:
        if self.database is None:
            raise ValueError("Database provider belum dikonfigurasi.")
        self.database.test_connection(config, progress=progress)

    def build(
        self, source_type: str, output: Path, *, input_file: Path | None = None,
        config: DatabaseConfig | None = None, progress: Progress = ignore_progress,
    ) -> StructureResult:
        output = output.resolve()
        if source_type not in {"Database", "Structure SQL", "Full SQL Backup"}:
            raise ValueError("Source Type tidak dikenal.")
        if source_type != "Database":
            if input_file is None or not input_file.is_file():
                raise ValueError("Pilih file input SQL yang dapat dibaca.")
            if input_file.resolve() == output or (output.exists() and input_file.samefile(output)):
                if source_type == "Structure SQL":
                    return self.validate(input_file, progress=progress)
                raise ValueError("Output harus berbeda dari file backup sumber.")
        progress("Validating structure..." if source_type == "Structure SQL" else "Processing SQL source...")
        descriptor, temporary = tempfile.mkstemp(prefix=".structure-", suffix=".sql", dir=output.parent)
        os.close(descriptor)
        staging = Path(temporary)
        removed = 0
        try:
            if source_type == "Database":
                if self.database is None or config is None:
                    raise ValueError("Lengkapi konfigurasi koneksi database.")
                progress("Reading database structure...")
                self.database.dump(config, staging, progress=progress)
            elif source_type == "Structure SQL":
                self.validate(input_file, progress=progress)
                progress("Copying structure SQL...")
                with input_file.open("rb") as source, staging.open("wb") as target:
                    reader = ProgressReader(source, os.fstat(source.fileno()).st_size, progress, "Copied")
                    shutil.copyfileobj(reader, target, length=1024 * 1024)
            else:
                progress("Opening backup SQL...")
                with input_file.open("rb") as source, staging.open("wb") as target:
                    size = os.fstat(source.fileno()).st_size
                    progress(f"File size: {size:,} bytes")
                    progress("Streaming SQL dump...")
                    _, removed = scan(ProgressReader(source, size, progress), target)
                progress(f"Skipped statements: {removed}")
            progress("Validating structure...")
            result = self.validate(staging, progress=progress)
            progress("Writing structure.sql...")
            os.replace(staging, output)
            logger.info("Structure completed: %d tables, %d bytes", result.table_count, result.size_bytes)
            return StructureResult(output, result.table_count, result.size_bytes, result.sha256, removed)
        finally:
            staging.unlink(missing_ok=True)
