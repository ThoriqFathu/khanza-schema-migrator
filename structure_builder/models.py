from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from .progress import Progress, ignore_progress


@dataclass(frozen=True)
class DatabaseConfig:
    host: str
    port: int
    database: str
    username: str
    password: str = field(repr=False)
    dump_executable: str = ""
    client_executable: str = ""


@dataclass(frozen=True)
class StructureResult:
    path: Path
    table_count: int
    size_bytes: int
    sha256: str
    removed_statements: int = 0


class DatabaseProvider(Protocol):
    def test_connection(self, config: DatabaseConfig, progress: Progress = ignore_progress) -> None: ...

    def dump(self, config: DatabaseConfig, destination: Path, progress: Progress = ignore_progress) -> None: ...
