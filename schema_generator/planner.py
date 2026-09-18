from .conflict import ConflictResolver
from .models import (
    ForeignKey,
    MigrationPlan,
    TableSchema,
)


def build_plan(
    existing: dict[str, TableSchema],
    khanza: dict[str, TableSchema],
    resolver: ConflictResolver | None = None,
) -> MigrationPlan:

    if resolver is None:
        resolver = ConflictResolver()

    plan = MigrationPlan()

    existing_names = set(existing)
    khanza_names = set(khanza)

    # ============================================================
    # CREATE TABLE
    # ============================================================

    for table_name in sorted(
        khanza_names - existing_names
    ):
        table = khanza[table_name]

        plan.create_tables.append(table)

        # Semua FK dari tabel baru tetap dimasukkan ke
        # add_foreign_keys.
        #
        # CREATE TABLE-nya sendiri akan dibuat tanpa FK.
        for foreign_key in sorted(
            table.foreign_keys.values(),
            key=lambda fk: fk.name,
        ):
            plan.add_foreign_keys.append(
                (
                    table_name,
                    foreign_key,
                )
            )

    # ============================================================
    # COMMON TABLES
    # ============================================================

    common_tables = sorted(
        existing_names & khanza_names
    )

    for table_name in common_tables:

        existing_table = existing[table_name]
        khanza_table = khanza[table_name]

        # ========================================================
        # COLUMNS
        # ========================================================

        existing_columns = set(
            existing_table.columns
        )

        khanza_columns = set(
            khanza_table.columns
        )

        # --------------------------------------------------------
        # DROP COLUMN
        # --------------------------------------------------------

        for column_name in sorted(
            existing_columns - khanza_columns
        ):
            plan.drop_columns.append(
                (
                    table_name,
                    column_name,
                    existing_table.columns[
                        column_name
                    ],
                )
            )

        # --------------------------------------------------------
        # ADD COLUMN
        # --------------------------------------------------------

        for column_name in sorted(
            khanza_columns - existing_columns
        ):
            plan.add_columns.append(
                (
                    table_name,
                    column_name,
                    khanza_table.columns[
                        column_name
                    ],
                )
            )

        # --------------------------------------------------------
        # MODIFY COLUMN
        # --------------------------------------------------------

        for column_name in sorted(
            existing_columns & khanza_columns
        ):
            existing_definition = (
                existing_table.columns[
                    column_name
                ]
            )

            khanza_definition = (
                khanza_table.columns[
                    column_name
                ]
            )

            if existing_definition == khanza_definition:
                continue

            conflict = resolver.resolve(
                object_type="column",
                table=table_name,
                name=column_name,
                existing=existing_definition,
                khanza=khanza_definition,
            )

            plan.conflicts.append(conflict)

            if conflict.decision == "K":
                plan.modify_columns.append(
                    (
                        table_name,
                        column_name,
                        existing_definition,
                        khanza_definition,
                    )
                )

        # ========================================================
        # INDEXES
        # ========================================================

        existing_indexes = set(
            existing_table.indexes
        )

        khanza_indexes = set(
            khanza_table.indexes
        )

        # --------------------------------------------------------
        # INDEX ONLY IN EXISTING
        # --------------------------------------------------------

        for index_name in sorted(
            existing_indexes - khanza_indexes
        ):
            if index_name.upper() == "PRIMARY":
                continue

            existing_definition = (
                existing_table.indexes[index_name]
            )

            conflict = resolver.resolve(
                object_type="index",
                table=table_name,
                name=index_name,
                existing=existing_definition,
                khanza="INDEX NOT PRESENT IN KHANZA",
            )

            plan.conflicts.append(conflict)

            if conflict.decision == "K":
                plan.drop_indexes.append(
                    (
                        table_name,
                        index_name,
                    )
                )

        # --------------------------------------------------------
        # INDEX ONLY IN KHANZA
        # --------------------------------------------------------

        for index_name in sorted(
            khanza_indexes - existing_indexes
        ):
            plan.add_indexes.append(
                (
                    table_name,
                    index_name,
                    khanza_table.indexes[
                        index_name
                    ],
                )
            )

        # --------------------------------------------------------
        # INDEX EXISTS IN BOTH BUT DIFFERENT
        # --------------------------------------------------------

        for index_name in sorted(
            existing_indexes & khanza_indexes
        ):
            existing_definition = (
                existing_table.indexes[index_name]
            )

            khanza_definition = (
                khanza_table.indexes[index_name]
            )

            if existing_definition == khanza_definition:
                continue

            # PRIMARY KEY tidak otomatis diganti.
            # PRIMARY KEY
            if index_name.upper() == "PRIMARY":
                conflict = resolver.resolve(
                    object_type="primary key",
                    table=table_name,
                    name=index_name,
                    existing=existing_definition,
                    khanza=khanza_definition,
                )

                plan.conflicts.append(conflict)

                if conflict.decision == "K":
                    plan.replace_indexes.append(
                        (
                            table_name,
                            index_name,
                            khanza_definition,
                        )
                    )

                continue

            conflict = resolver.resolve(
                object_type="index",
                table=table_name,
                name=index_name,
                existing=existing_definition,
                khanza=khanza_definition,
            )

            plan.conflicts.append(conflict)

            if conflict.decision == "K":
                plan.replace_indexes.append(
                    (
                        table_name,
                        index_name,
                        khanza_definition,
                    )
                )

        # ========================================================
        # FOREIGN KEYS
        # ========================================================

        existing_fks = set(
            existing_table.foreign_keys
        )

        khanza_fks = set(
            khanza_table.foreign_keys
        )

        # --------------------------------------------------------
        # FK ONLY IN EXISTING
        # --------------------------------------------------------

        for fk_name in sorted(
            existing_fks - khanza_fks
        ):
            existing_fk = (
                existing_table.foreign_keys[
                    fk_name
                ]
            )

            existing_definition = (
                foreign_key_signature_text(
                    existing_fk
                )
            )

            conflict = resolver.resolve(
                object_type="foreign key",
                table=table_name,
                name=fk_name,
                existing=existing_definition,
                khanza="FOREIGN KEY NOT PRESENT IN KHANZA",
            )

            plan.conflicts.append(conflict)

            if conflict.decision == "K":
                plan.drop_foreign_keys.append(
                    (
                        table_name,
                        fk_name,
                    )
                )

        # --------------------------------------------------------
        # FK ONLY IN KHANZA
        # --------------------------------------------------------

        for fk_name in sorted(
            khanza_fks - existing_fks
        ):
            plan.add_foreign_keys.append(
                (
                    table_name,
                    khanza_table.foreign_keys[
                        fk_name
                    ],
                )
            )

        # --------------------------------------------------------
        # FK EXISTS IN BOTH BUT DIFFERENT
        # --------------------------------------------------------

        for fk_name in sorted(
            existing_fks & khanza_fks
        ):
            existing_fk = (
                existing_table.foreign_keys[
                    fk_name
                ]
            )

            khanza_fk = (
                khanza_table.foreign_keys[
                    fk_name
                ]
            )

            if (
                existing_fk.signature()
                == khanza_fk.signature()
            ):
                continue

            existing_definition = (
                foreign_key_signature_text(
                    existing_fk
                )
            )

            khanza_definition = (
                foreign_key_signature_text(
                    khanza_fk
                )
            )

            conflict = resolver.resolve(
                object_type="foreign key",
                table=table_name,
                name=fk_name,
                existing=existing_definition,
                khanza=khanza_definition,
            )

            plan.conflicts.append(conflict)

            if conflict.decision == "K":

                plan.drop_foreign_keys.append(
                    (
                        table_name,
                        fk_name,
                    )
                )

                plan.add_foreign_keys.append(
                    (
                        table_name,
                        khanza_fk,
                    )
                )

        # ========================================================
        # REPORT
        # ========================================================

        plan.kept.append(table_name)

    return plan


def foreign_key_signature_text(
    foreign_key: ForeignKey,
) -> str:

    columns = ", ".join(
        f"`{column}`"
        for column in foreign_key.columns
    )

    referenced_columns = ", ".join(
        f"`{column}`"
        for column in foreign_key.referenced_columns
    )

    result = (
        f"FOREIGN KEY ({columns}) "
        f"REFERENCES "
        f"`{foreign_key.referenced_table}` "
        f"({referenced_columns})"
    )

    if foreign_key.on_delete:
        result += (
            f" ON DELETE {foreign_key.on_delete}"
        )

    if foreign_key.on_update:
        result += (
            f" ON UPDATE {foreign_key.on_update}"
        )

    return result