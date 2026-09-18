from .models import MigrationPlan


def print_summary(
    plan: MigrationPlan,
    output_file: str,
    cycles: list[list[str]] | None = None,
) -> None:

    print()
    print("=" * 80)
    print("MIGRATION PLAN")
    print("=" * 80)

    print(
        f"CREATE TABLE        : {len(plan.create_tables)}"
    )

    print(
        f"DROP FOREIGN KEY    : {len(plan.drop_foreign_keys)}"
    )

    print(
        f"DROP COLUMN         : {len(plan.drop_columns)}"
    )

    print(
        f"ADD COLUMN          : {len(plan.add_columns)}"
    )

    print(
        f"MODIFY COLUMN       : {len(plan.modify_columns)}"
    )

    print(
        f"DROP INDEX          : {len(plan.drop_indexes)}"
    )

    print(
        f"ADD / REPLACE INDEX : {len(plan.add_indexes)}"
    )

    print(
        f"ADD FOREIGN KEY     : {len(plan.add_foreign_keys)}"
    )

    print(
        f"CONFLICTS           : {len(plan.conflicts)}"
    )

    print(
        f"KEPT                : {len(plan.kept)}"
    )

    if cycles:

        print()
        print(
            "WARNING: Foreign-key dependency cycle detected:"
        )

        for cycle in cycles:

            print(
                "  - " + " -> ".join(cycle)
            )

    print()
    print("Migration written to:")
    print(f"  {output_file}")

    print()
    print("IMPORTANT:")

    print(
        f"Review {output_file} before executing it."
    )

    print(
        "This script does NOT modify any database."
    )