import re

from .models import ForeignKey, TableSchema


CREATE_TABLE_RE = re.compile(
    r"^CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?`([^`]+)`",
    re.IGNORECASE,
)

COLUMN_RE = re.compile(
    r"^`([^`]+)`\s+(.+)$"
)

INDEX_RE = re.compile(
    r"^(PRIMARY KEY|UNIQUE KEY|KEY|FULLTEXT KEY|SPATIAL KEY)"
    r"(?:\s+`([^`]+)`)?",
    re.IGNORECASE,
)

FOREIGN_KEY_RE = re.compile(
    r"""
    CONSTRAINT\s+`(?P<name>[^`]+)`
    \s+
    FOREIGN\s+KEY\s*
    \(
        (?P<columns>[^)]+)
    \)
    \s+
    REFERENCES\s+`(?P<ref_table>[^`]+)`
    \s*
    \(
        (?P<ref_columns>[^)]+)
    \)
    (?P<actions>.*?)
    (?=
        ,\s*CONSTRAINT
        |
        \s*\)\s*(?:ENGINE|TYPE|;)
    )
    """,
    re.IGNORECASE | re.DOTALL | re.VERBOSE,
)

ON_DELETE_RE = re.compile(
    r"\bON\s+DELETE\s+(CASCADE|SET\s+NULL|RESTRICT|NO\s+ACTION)",
    re.IGNORECASE,
)

ON_UPDATE_RE = re.compile(
    r"\bON\s+UPDATE\s+(CASCADE|SET\s+NULL|RESTRICT|NO\s+ACTION)",
    re.IGNORECASE,
)


def normalize(value: str) -> str:
    return " ".join(value.strip().split())


def normalize_action(value: str | None) -> str | None:
    if value is None:
        return None

    return normalize(value).upper()


def parse_column_list(value: str) -> tuple[str, ...]:
    return tuple(
        item.strip().strip("`")
        for item in value.split(",")
        if item.strip()
    )


def parse_search(search: str | None) -> list[str]:
    if not search:
        return []

    return [
        item.strip().lower()
        for item in search.split(",")
        if item.strip()
    ]


def table_matches(
    table_name: str,
    keywords: list[str],
) -> bool:

    if not keywords:
        return True

    name = table_name.lower()

    return any(
        keyword in name
        for keyword in keywords
    )


def read_create_table(
    handle,
    first_line: str,
) -> str:

    lines = [first_line]

    for line in handle:
        lines.append(line)

        if re.match(
            r"^\)\s*(?:ENGINE|TYPE|;)",
            line.strip(),
            re.IGNORECASE,
        ):
            break

    return "".join(lines)


def extract_columns(
    definition: str,
) -> dict[str, str]:

    columns = {}

    for line in definition.splitlines():

        line = line.strip().rstrip(",")

        match = COLUMN_RE.match(line)

        if not match:
            continue

        name, column_definition = match.groups()

        columns[name] = normalize(
            column_definition
        )

    return columns


def extract_indexes(
    definition: str,
) -> dict[str, str]:

    indexes = {}

    for line in definition.splitlines():

        line = line.strip().rstrip(",")

        match = INDEX_RE.match(line)

        if not match:
            continue

        index_type, index_name = match.groups()

        if index_type.upper() == "PRIMARY KEY":
            key = "PRIMARY"
        else:
            key = index_name

        if key is None:
            continue

        indexes[key] = normalize_index_definition(
            index_type,
            line,
        )

    return indexes


def extract_foreign_keys(
    definition: str,
) -> dict[str, ForeignKey]:

    foreign_keys = {}

    for match in FOREIGN_KEY_RE.finditer(definition):

        name = match.group("name")

        columns = parse_column_list(
            match.group("columns")
        )

        referenced_columns = parse_column_list(
            match.group("ref_columns")
        )

        actions = match.group("actions")

        delete_match = ON_DELETE_RE.search(
            actions
        )

        update_match = ON_UPDATE_RE.search(
            actions
        )

        on_delete = (
            normalize_action(
                delete_match.group(1)
            )
            if delete_match
            else None
        )

        on_update = (
            normalize_action(
                update_match.group(1)
            )
            if update_match
            else None
        )

        foreign_keys[name] = ForeignKey(
            name=name,
            columns=columns,
            referenced_table=match.group(
                "ref_table"
            ),
            referenced_columns=referenced_columns,
            on_delete=on_delete,
            on_update=on_update,
        )

    return foreign_keys


def extract_dependencies(
    definition: str,
) -> set[str]:

    return {
        foreign_key.referenced_table
        for foreign_key
        in extract_foreign_keys(definition).values()
    }


def parse_table(
    name: str,
    definition: str,
) -> TableSchema:

    foreign_keys = extract_foreign_keys(
        definition
    )

    return TableSchema(
        name=name,
        definition=definition,
        columns=extract_columns(definition),
        indexes=extract_indexes(definition),
        foreign_keys=foreign_keys,
        dependencies={
            foreign_key.referenced_table
            for foreign_key in foreign_keys.values()
        },
    )


def extract_tables(
    filename: str,
    search: str | None = None,
) -> dict[str, TableSchema]:

    keywords = parse_search(search)

    tables = {}

    with open(
        filename,
        "r",
        encoding="utf-8",
        errors="ignore",
    ) as handle:

        for line in handle:

            match = CREATE_TABLE_RE.match(
                line.strip()
            )

            if not match:
                continue

            table_name = match.group(1)

            definition = read_create_table(
                handle,
                line,
            )

            if not table_matches(
                table_name,
                keywords,
            ):
                continue

            tables[table_name] = parse_table(
                table_name,
                definition,
            )

    return tables

def normalize_index_definition(
    index_type: str,
    line: str,
) -> str:
    line = normalize(line)

    # USING BTREE adalah default dan tidak dianggap
    # sebagai perbedaan struktur index.
    line = re.sub(
        r"\s+USING\s+BTREE\b",
        "",
        line,
        flags=re.IGNORECASE,
    )

    if index_type.upper() == "PRIMARY KEY":
        match = re.search(
            r"\(([^)]+)\)",
            line,
        )

        if not match:
            return line

        columns = ", ".join(
            f"`{column}`"
            for column in parse_column_list(
                match.group(1)
            )
        )

        return f"PRIMARY KEY ({columns})"

    return line