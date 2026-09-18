from .models import MigrationPlan
from .sql import (
    generate_add_column,
    generate_add_foreign_key,
    generate_add_index,
    generate_create_table,
    generate_drop_column,
    generate_drop_foreign_key,
    generate_drop_index,
    generate_modify_column,
    generate_replace_index,
)


def write_migration(
    plan: MigrationPlan,
    filename: str,
    cycles: list[list[str]] | None = None,
) -> None:

    cycles = cycles or []

    with open(
        filename,
        "w",
        encoding="utf-8",
    ) as handle:

        handle.write(
            "-- ============================================================\n"
        )
        handle.write(
            "-- GENERATED SCHEMA MIGRATION\n"
        )
        handle.write(
            "-- ============================================================\n"
        )
        handle.write("\n")

        # ========================================================
        # 1. CREATE TABLE
        # ========================================================

        if plan.create_tables:

            handle.write(
                "-- ============================================================\n"
            )
            handle.write(
                "-- CREATE TABLE\n"
            )
            handle.write(
                "-- ============================================================\n"
            )

            for table in plan.create_tables:

                handle.write(
                    generate_create_table(table)
                    + "\n"
                )

            handle.write("\n")

        # ========================================================
        # 2. DROP FOREIGN KEY
        # ========================================================

        if plan.drop_foreign_keys:

            handle.write(
                "-- ============================================================\n"
            )
            handle.write(
                "-- DROP FOREIGN KEY\n"
            )
            handle.write(
                "-- ============================================================\n"
            )

            for table, name in sorted(
                plan.drop_foreign_keys
            ):

                handle.write(
                    generate_drop_foreign_key(
                        table,
                        name,
                    )
                    + "\n"
                )

            handle.write("\n")

        # ========================================================
        # 3. ADD COLUMN
        # ========================================================

        if plan.add_columns:

            handle.write(
                "-- ============================================================\n"
            )
            handle.write(
                "-- ADD COLUMN\n"
            )
            handle.write(
                "-- ============================================================\n"
            )

            for (
                table,
                column,
                definition,
            ) in sorted(
                plan.add_columns
            ):

                handle.write(
                    generate_add_column(
                        table,
                        column,
                        definition,
                    )
                    + "\n"
                )

            handle.write("\n")

        # ========================================================
        # 4. REPLACE INDEX
        # ========================================================

        if plan.replace_indexes:

            handle.write(
                "-- ============================================================\n"
            )
            handle.write(
                "-- REPLACE INDEX\n"
            )
            handle.write(
                "-- ============================================================\n"
            )

            for (
                table,
                index_name,
                definition,
            ) in sorted(
                plan.replace_indexes
            ):

                handle.write(
                    generate_replace_index(
                        table,
                        index_name,
                        definition,
                    )
                    + "\n"
                )

            handle.write("\n")

        # ========================================================
        # 5. DROP INDEX
        # ========================================================

        if plan.drop_indexes:

            handle.write(
                "-- ============================================================\n"
            )
            handle.write(
                "-- DROP INDEX\n"
            )
            handle.write(
                "-- ============================================================\n"
            )

            for (
                table,
                index_name,
            ) in sorted(
                plan.drop_indexes
            ):

                handle.write(
                    generate_drop_index(
                        table,
                        index_name,
                    )
                    + "\n"
                )

            handle.write("\n")

        # ========================================================
        # 6. DROP COLUMN
        # ========================================================

        if plan.drop_columns:

            handle.write(
                "-- ============================================================\n"
            )
            handle.write(
                "-- DROP COLUMN\n"
            )
            handle.write(
                "-- ============================================================\n"
            )

            for (
                table,
                column,
                _definition,
            ) in sorted(
                plan.drop_columns
            ):

                handle.write(
                    generate_drop_column(
                        table,
                        column,
                    )
                    + "\n"
                )

            handle.write("\n")

        # ========================================================
        # 7. MODIFY COLUMN
        # ========================================================

        if plan.modify_columns:

            handle.write(
                "-- ============================================================\n"
            )
            handle.write(
                "-- MODIFY COLUMN\n"
            )
            handle.write(
                "-- ============================================================\n"
            )

            for (
                table,
                column,
                _existing_definition,
                khanza_definition,
            ) in sorted(
                plan.modify_columns
            ):

                handle.write(
                    generate_modify_column(
                        table,
                        column,
                        khanza_definition,
                    )
                    + "\n"
                )

            handle.write("\n")

        # ========================================================
        # 8. ADD INDEX
        # ========================================================

        if plan.add_indexes:

            handle.write(
                "-- ============================================================\n"
            )
            handle.write(
                "-- ADD INDEX\n"
            )
            handle.write(
                "-- ============================================================\n"
            )

            for (
                table,
                _index_name,
                definition,
            ) in sorted(
                plan.add_indexes
            ):

                handle.write(
                    generate_add_index(
                        table,
                        definition,
                    )
                    + "\n"
                )

            handle.write("\n")

        # ========================================================
        # 9. ADD FOREIGN KEY
        # ========================================================

        if plan.add_foreign_keys:

            handle.write(
                "-- ============================================================\n"
            )
            handle.write(
                "-- ADD FOREIGN KEY\n"
            )
            handle.write(
                "-- ============================================================\n"
            )

            for (
                table,
                foreign_key,
            ) in sorted(
                plan.add_foreign_keys,
                key=lambda item: (
                    item[0],
                    item[1].name,
                ),
            ):

                handle.write(
                    generate_add_foreign_key(
                        table,
                        foreign_key,
                    )
                    + "\n"
                )

            handle.write("\n")

        # ========================================================
        # 10. DEPENDENCY CYCLES WARNING
        # ========================================================

        if cycles:

            handle.write(
                "-- ============================================================\n"
            )
            handle.write(
                "-- WARNING: TABLE DEPENDENCY CYCLES\n"
            )
            handle.write(
                "-- ============================================================\n"
            )

            for cycle in cycles:

                handle.write(
                    "-- "
                    + " -> ".join(cycle)
                    + "\n"
                )

            handle.write("\n")

        # ========================================================
        # END
        # ========================================================

        handle.write(
            "-- ============================================================\n"
        )
        handle.write(
            "-- END OF MIGRATION\n"
        )
        handle.write(
            "-- ============================================================\n"
        )