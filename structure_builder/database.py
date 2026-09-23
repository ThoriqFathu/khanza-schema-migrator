"""Read-only client adapter. Credentials never appear in process arguments."""
import os
import shutil
import subprocess
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from .models import DatabaseConfig
from .progress import Progress, ignore_progress


def _executable(configured: str, names: tuple[str, ...]) -> str:
    if configured:
        found = shutil.which(configured)
        if found:
            return found
    else:
        for name in names:
            found = shutil.which(name)
            if found:
                return found
    raise ValueError(
        f"{names[0]} tidak ditemukan. Install MySQL/MariaDB client tools "
        "atau konfigurasi path executable pada tab Structure Builder."
    )


def _option(value: str) -> str:
    if "\x00" in value:
        raise ValueError("Konfigurasi database mengandung karakter NUL.")
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r") + '"'


@contextmanager
def _credentials(config: DatabaseConfig) -> Iterator[str]:
    if not config.host.strip() or not config.database.strip() or not config.username.strip():
        raise ValueError("Host, Database, dan Username wajib diisi.")
    if not 1 <= config.port <= 65535:
        raise ValueError("Port harus antara 1 dan 65535.")
    if config.database.startswith("-"):
        raise ValueError("Nama database tidak boleh diawali '-'.")
    try:
        with tempfile.TemporaryDirectory(prefix="khanza-client-") as directory:
            path = Path(directory) / "client.cnf"
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write("[client]\n")
                for name, value in (
                    ("host", config.host), ("port", str(config.port)),
                    ("user", config.username), ("password", config.password),
                ):
                    handle.write(f"{name}={_option(value)}\n")
                handle.write("protocol=tcp\n")
            yield str(path)
    except OSError:
        raise ValueError(
            "Tidak dapat mengakses file temporary/output client. Periksa izin dan ruang disk."
        ) from None



class MysqlDumpProvider:
    def _run(self, args: list[str], output: object, timeout: int,
             progress: Progress = ignore_progress, activity: str = "Database client") -> None:
        # Only fixed activity messages and observed sizes are reported. Raw stderr
        # can contain secrets; discard it, and determine success by return code.
        try:
            with subprocess.Popen(
                args, stdout=output, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL,
            ) as process:
                try:
                    progress(f"{activity} process started.")
                    deadline = time.monotonic() + timeout
                    while True:
                        remaining = deadline - time.monotonic()
                        if remaining <= 0:
                            raise subprocess.TimeoutExpired(args, timeout)
                        try:
                            returncode = process.wait(timeout=min(2.0, remaining))
                            break
                        except subprocess.TimeoutExpired:
                            if hasattr(output, "fileno"):
                                size = os.fstat(output.fileno()).st_size
                                progress(f"{activity} still running; output: {size:,} bytes")
                            else:
                                progress(f"{activity} still running...")
                finally:
                    if process.poll() is None:
                        process.kill()
                        process.wait()
        except subprocess.TimeoutExpired:
            raise ValueError("Client database timeout. Periksa jaringan/server dan coba kembali.") from None
        except OSError:
            raise ValueError("Client database gagal dijalankan. Periksa path dan izin executable.") from None
        if returncode:
            raise ValueError(
                f"Client database exited with code {returncode}. Periksa host/port, credential, nama database, "
                "izin metadata/routines/events, dan kecocokan versi client dengan server."
            )
        progress(f"{activity} completed.")

    def test_connection(self, config: DatabaseConfig, progress: Progress = ignore_progress) -> None:
        progress("Checking mysql / mariadb client...")
        client = _executable(config.client_executable, ("mysql", "mariadb"))
        progress("SQL client found.")
        progress("Testing database connection...")
        with _credentials(config) as credentials:
            self._run([
                client, f"--defaults-file={credentials}", "--connect-timeout=10",
                f"--database={config.database}", "--batch", "--execute=SELECT 1",
            ], subprocess.DEVNULL, 20, progress, "Connection test")
        progress("Connection successful.")

    def dump(self, config: DatabaseConfig, destination: Path, progress: Progress = ignore_progress) -> None:
        progress("Checking mysqldump / mariadb-dump...")
        client = _executable(config.dump_executable, ("mysqldump", "mariadb-dump"))
        progress("Dump client found.")
        progress("Reading database structure...")
        with _credentials(config) as credentials, destination.open("wb") as output:
            self._run([
                client, f"--defaults-file={credentials}", "--no-data", "--routines",
                "--triggers", "--events", "--skip-lock-tables", "--no-tablespaces",
                "--default-character-set=utf8mb4", config.database,
            ], output, 3600, progress, "Dump")
