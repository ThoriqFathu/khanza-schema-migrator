from dataclasses import dataclass, field


@dataclass(frozen=True)
class ForeignKey:
    name: str
    columns: tuple[str, ...]
    referenced_table: str
    referenced_columns: tuple[str, ...]
    on_delete: str | None = None
    on_update: str | None = None

    def signature(self) -> tuple:
        return (
            self.columns,
            self.referenced_table,
            self.referenced_columns,
            self.on_delete,
            self.on_update,
        )


@dataclass
class TableSchema:
    name: str
    definition: str
    columns: dict[str, str] = field(default_factory=dict)
    indexes: dict[str, str] = field(default_factory=dict)
    foreign_keys: dict[str, ForeignKey] = field(
        default_factory=dict
    )
    dependencies: set[str] = field(
        default_factory=set
    )


@dataclass
class Conflict:
    object_type: str
    table: str
    name: str
    existing: str
    khanza: str
    decision: str


@dataclass
class MigrationPlan:
    # ============================================================
    # CREATE TABLE
    # ============================================================

    create_tables: list[TableSchema] = field(
        default_factory=list
    )

    # ============================================================
    # FOREIGN KEY
    # ============================================================

    drop_foreign_keys: list[tuple[str, str]] = field(
        default_factory=list
    )

    add_foreign_keys: list[tuple[str, ForeignKey]] = field(
        default_factory=list
    )

    # ============================================================
    # COLUMNS
    # ============================================================

    drop_columns: list[tuple[str, str, str]] = field(
        default_factory=list
    )

    add_columns: list[tuple[str, str, str]] = field(
        default_factory=list
    )

    modify_columns: list[tuple[str, str, str, str]] = field(
        default_factory=list
    )

    # ============================================================
    # INDEX
    # ============================================================

    drop_indexes: list[tuple[str, str]] = field(
        default_factory=list
    )

    add_indexes: list[tuple[str, str, str]] = field(
        default_factory=list
    )

    replace_indexes: list[tuple[str, str, str]] = field(
        default_factory=list
    )

    # ============================================================
    # REPORT
    # ============================================================

    conflicts: list[Conflict] = field(
        default_factory=list
    )

    kept: list[str] = field(
        default_factory=list
    )