from schema_generator.application.migration_service import (
    MigrationService,
)
from schema_generator.conflict import ConflictDecision


def conflict_handler(
    object_type: str,
    table: str,
    name: str,
    existing: str,
    khanza: str,
) -> ConflictDecision:

    print()
    print("=" * 60)
    print("CONFLICT")
    print("=" * 60)
    print(f"Type     : {object_type}")
    print(f"Table    : {table}")
    print(f"Name     : {name}")
    print()
    print(f"Existing : {existing}")
    print(f"Khanza   : {khanza}")
    print()

    print("[E] Keep Existing")
    print("[K] Use Khanza")
    print("[S] Skip")
    print("[T] Use this choice for this table")

    while True:
        choice = input(
            "Choice [E/K/S/T]: "
        ).strip().upper()

        if choice in {"E", "K", "S", "T"}:
            break

        print(
            "Pilihan tidak valid. "
            "Gunakan E, K, S, atau T."
        )

    if choice == "T":

        while True:
            decision = input(
                "Choice untuk semua conflict "
                "tabel ini [E/K/S]: "
            ).strip().upper()

            if decision in {"E", "K", "S"}:
                break

            print(
                "Pilihan tidak valid. "
                "Gunakan E, K, atau S."
            )

        return ConflictDecision(
            decision=decision,
            remember_for_table=True,
        )

    return ConflictDecision(
        decision=choice,
        remember_for_table=False,
    )


service = MigrationService()

result = service.generate(
    existing_file="existing.sql",
    khanza_file="khanza.sql",
    output_file="migration.sql",
    conflict_callback=conflict_handler,
)

print()
print("Migration selesai.")
print(
    f"Conflicts: {len(result.plan.conflicts)}"
)