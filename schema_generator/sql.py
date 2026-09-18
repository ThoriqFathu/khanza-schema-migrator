import re

from .models import ForeignKey, TableSchema


def quote_identifier(name: str) -> str:
    return f"`{name.replace('`', '``')}`"


def generate_create_table(
    table: TableSchema,
) -> str:
    """
    Generate CREATE TABLE tanpa FOREIGN KEY.

    FOREIGN KEY akan dibuat terpisah pada bagian
    ADD FOREIGN KEY di akhir migration.
    """

    definition = table.definition.strip().rstrip(";")

    definition = remove_foreign_key_constraints(
        definition
    )

    return definition + ";"


def remove_foreign_key_constraints(
    definition: str,
) -> str:
    """
    Menghapus CONSTRAINT ... FOREIGN KEY ... dari
    CREATE TABLE.

    Contoh:

        CONSTRAINT `xxx`
            FOREIGN KEY (`nip`)
            REFERENCES `petugas` (`nip`)
            ON DELETE CASCADE
            ON UPDATE CASCADE

    akan dihapus dari CREATE TABLE.

    Foreign key tetap tersedia di:
        TableSchema.foreign_keys
    """

    pattern = re.compile(
        r"""
        ,\s*
        CONSTRAINT\s+`[^`]+`
        \s+
        FOREIGN\s+KEY\s*
        \(
            [^)]+
        \)
        \s+
        REFERENCES\s+`[^`]+`
        \s*
        \(
            [^)]+
        \)
        (?:
            \s+
            ON\s+(?:DELETE|UPDATE)
            \s+
            (?:CASCADE|SET\s+NULL|RESTRICT|NO\s+ACTION)
        )*
        """,
        re.IGNORECASE | re.DOTALL | re.VERBOSE,
    )

    result = pattern.sub("", definition)

    return result


def generate_add_column(
    table: str,
    column: str,
    definition: str,
) -> str:
    return (
        f"ALTER TABLE {quote_identifier(table)} "
        f"ADD COLUMN {quote_identifier(column)} "
        f"{definition};"
    )


def generate_drop_column(
    table: str,
    column: str,
) -> str:
    return (
        f"ALTER TABLE {quote_identifier(table)} "
        f"DROP COLUMN {quote_identifier(column)};"
    )


def generate_modify_column(
    table: str,
    column: str,
    definition: str,
) -> str:
    return (
        f"ALTER TABLE {quote_identifier(table)} "
        f"MODIFY COLUMN {quote_identifier(column)} "
        f"{definition};"
    )


def generate_add_index(
    table: str,
    definition: str,
) -> str:
    return (
        f"ALTER TABLE {quote_identifier(table)} "
        f"ADD {definition};"
    )


def generate_drop_index(
    table: str,
    index_name: str,
) -> str:

    if index_name.upper() == "PRIMARY":
        raise ValueError(
            "PRIMARY KEY tidak boleh dihapus otomatis."
        )

    return (
        f"ALTER TABLE {quote_identifier(table)} "
        f"DROP INDEX {quote_identifier(index_name)};"
    )


def generate_replace_index(
    table: str,
    index_name: str,
    definition: str,
) -> str:

    if index_name.upper() == "PRIMARY":
        return (
            f"ALTER TABLE {quote_identifier(table)} "
            f"DROP PRIMARY KEY, "
            f"ADD {definition};"
        )

    return (
        f"ALTER TABLE {quote_identifier(table)} "
        f"DROP INDEX {quote_identifier(index_name)}, "
        f"ADD {definition};"
    )


def generate_drop_foreign_key(
    table: str,
    name: str,
) -> str:
    return (
        f"ALTER TABLE {quote_identifier(table)} "
        f"DROP FOREIGN KEY {quote_identifier(name)};"
    )


def generate_add_foreign_key(
    table: str,
    foreign_key: ForeignKey,
) -> str:

    columns = ", ".join(
        quote_identifier(column)
        for column in foreign_key.columns
    )

    referenced_columns = ", ".join(
        quote_identifier(column)
        for column in foreign_key.referenced_columns
    )

    sql = (
        f"ALTER TABLE {quote_identifier(table)} "
        f"ADD CONSTRAINT "
        f"{quote_identifier(foreign_key.name)} "
        f"FOREIGN KEY ({columns}) "
        f"REFERENCES "
        f"{quote_identifier(foreign_key.referenced_table)} "
        f"({referenced_columns})"
    )

    if foreign_key.on_delete:
        sql += (
            f" ON DELETE {foreign_key.on_delete}"
        )

    if foreign_key.on_update:
        sql += (
            f" ON UPDATE {foreign_key.on_update}"
        )

    return sql + ";"