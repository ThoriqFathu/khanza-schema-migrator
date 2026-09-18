from dataclasses import dataclass

from ..conflict import ConflictCallback, ConflictResolver
from ..dependency import order_tables
from ..models import MigrationPlan
from ..parser import extract_tables
from ..planner import build_plan
from ..writer import write_migration


@dataclass
class MigrationResult:
    plan: MigrationPlan
    cycles: list[list[str]]
    existing_table_count: int
    khanza_table_count: int
    output_file: str


class MigrationService:
    def generate(
        self,
        existing_file: str,
        khanza_file: str,
        output_file: str,
        search: str | None = None,
        conflict_callback: ConflictCallback | None = None,
    ) -> MigrationResult:

        resolver = ConflictResolver(
            callback=conflict_callback,
        )

        existing = extract_tables(
            existing_file,
            search,
        )

        khanza = extract_tables(
            khanza_file,
            search,
        )

        plan = build_plan(
            existing,
            khanza,
            resolver=resolver,
        )

        ordered_tables, cycles = order_tables(
            plan.create_tables,
        )

        plan.create_tables = ordered_tables

        write_migration(
            plan,
            output_file,
            cycles,
        )

        return MigrationResult(
            plan=plan,
            cycles=cycles,
            existing_table_count=len(existing),
            khanza_table_count=len(khanza),
            output_file=output_file,
        )