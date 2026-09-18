#!/usr/bin/env python3

import argparse

from schema_generator.application.migration_service import (
    MigrationService,
)
from schema_generator.summary import print_summary


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Generate safe SQL migration "
            "from Khanza schema."
        )
    )

    parser.add_argument(
        "existing_file",
        help="Existing database SQL structure",
    )

    parser.add_argument(
        "khanza_file",
        help="Khanza database SQL",
    )

    parser.add_argument(
        "--search",
        help="Filter table names, comma separated",
    )

    parser.add_argument(
        "--output",
        "-o",
        default="migration.sql",
        help="Output migration SQL",
    )

    args = parser.parse_args()

    print("=" * 80)
    print("SCHEMA MIGRATION GENERATOR")
    print("=" * 80)

    service = MigrationService()

    print()
    print("Reading Existing schema...")

    result = service.generate(
        existing_file=args.existing_file,
        khanza_file=args.khanza_file,
        output_file=args.output,
        search=args.search,
    )

    print(
        f"  Existing tables : "
        f"{result.existing_table_count}"
    )

    print(
        f"  Khanza tables   : "
        f"{result.khanza_table_count}"
    )

    print_summary(
        result.plan,
        result.output_file,
        result.cycles,
    )


if __name__ == "__main__":
    main()