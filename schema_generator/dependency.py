from collections import defaultdict

from .models import TableSchema


def order_tables(
    tables: list[TableSchema],
) -> tuple[list[TableSchema], list[list[str]]]:

    table_map = {
        table.name: table
        for table in tables
    }

    # Hanya dependency yang juga akan dibuat dalam migration.
    dependencies = {
        table.name: {
            dependency
            for dependency in table.dependencies
            if dependency in table_map
            and dependency != table.name
        }
        for table in tables
    }

    reverse_dependencies = defaultdict(set)

    for table_name, deps in dependencies.items():
        for dependency in deps:
            reverse_dependencies[dependency].add(table_name)

    ready = sorted(
        table_name
        for table_name, deps in dependencies.items()
        if not deps
    )

    ordered_names = []

    while ready:
        current = ready.pop(0)

        ordered_names.append(current)

        for dependent in sorted(
            reverse_dependencies[current]
        ):
            dependencies[dependent].discard(current)

            if not dependencies[dependent]:
                ready.append(dependent)

        ready.sort()

    cycles = []

    remaining = {
        name: sorted(deps)
        for name, deps in dependencies.items()
        if deps
    }

    if remaining:
        cycles.append(
            sorted(remaining.keys())
        )

        # Fallback deterministic.
        ordered_names.extend(
            sorted(remaining.keys())
        )

    return (
        [table_map[name] for name in ordered_names],
        cycles,
    )