"""Excel-to-web app converter: upload .xlsx, detect schema, generate CRUD app."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd


@dataclass
class ColumnSchema:
    """Detected schema for a single column."""

    name: str
    dtype: str  # "text", "integer", "float", "date", "boolean"
    nullable: bool = True
    sample_values: list[str] = field(default_factory=list)


@dataclass
class TableSchema:
    """Detected schema for a full table."""

    table_name: str
    columns: list[ColumnSchema]
    row_count: int = 0


def detect_column_dtype(series: pd.Series) -> str:
    """Detect the best column type for a pandas Series."""
    if pd.api.types.is_bool_dtype(series):
        return "boolean"
    if pd.api.types.is_integer_dtype(series):
        return "integer"
    if pd.api.types.is_float_dtype(series):
        return "float"
    if pd.api.types.is_datetime64_any_dtype(series):
        return "date"

    # Try parsing as dates
    non_null = series.dropna()
    if len(non_null) > 0:
        try:
            pd.to_datetime(non_null.head(20))
            return "date"
        except (ValueError, TypeError):
            pass

    return "text"


def detect_schema(df: pd.DataFrame, table_name: str = "data") -> TableSchema:
    """Detect the schema of a DataFrame."""
    columns = []
    for col in df.columns:
        dtype = detect_column_dtype(df[col])
        sample = [str(v) for v in df[col].dropna().head(3).tolist()]
        columns.append(
            ColumnSchema(
                name=str(col),
                dtype=dtype,
                nullable=df[col].isna().any(),
                sample_values=sample,
            )
        )
    return TableSchema(table_name=table_name, columns=columns, row_count=len(df))


def read_excel(path: str | Path) -> dict[str, pd.DataFrame]:
    """Read an Excel file, returning {sheet_name: DataFrame}."""
    path = Path(path)
    if path.suffix in (".csv", ".tsv"):
        sep = "\t" if path.suffix == ".tsv" else ","
        return {"Sheet1": pd.read_csv(path, sep=sep)}
    xls = pd.ExcelFile(path)
    return {name: xls.parse(name) for name in xls.sheet_names}


def create_sqlite_db(df: pd.DataFrame, table_name: str, db_path: str | Path) -> TableSchema:
    """Create a SQLite database from a DataFrame."""
    db_path = Path(db_path)
    schema = detect_schema(df, table_name)

    type_map = {
        "text": "TEXT",
        "integer": "INTEGER",
        "float": "REAL",
        "date": "TEXT",
        "boolean": "INTEGER",
    }

    col_defs = []
    col_defs.append("id INTEGER PRIMARY KEY AUTOINCREMENT")
    for col in schema.columns:
        null = "" if col.nullable else " NOT NULL"
        col_defs.append(f'"{col.name}" {type_map[col.dtype]}{null}')

    create_sql = f'CREATE TABLE IF NOT EXISTS "{table_name}" ({", ".join(col_defs)})'

    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute(create_sql)
        # Insert data
        clean_df = df.copy()
        for col in schema.columns:
            if col.dtype == "boolean":
                clean_df[col.name] = clean_df[col.name].astype(int)
            elif col.dtype == "date":
                clean_df[col.name] = clean_df[col.name].astype(str)

        placeholders = ", ".join(["?"] * len(schema.columns))
        col_names = ", ".join(f'"{c.name}"' for c in schema.columns)
        insert_sql = f'INSERT INTO "{table_name}" ({col_names}) VALUES ({placeholders})'

        for _, row in clean_df.iterrows():
            values = [None if pd.isna(row[col.name]) else row[col.name] for col in schema.columns]
            conn.execute(insert_sql, values)
        conn.commit()
    finally:
        conn.close()

    return schema


def generate_streamlit_code(schema: TableSchema, db_path: str = "data.db") -> str:
    """Generate a Streamlit CRUD app from a table schema."""
    lines = [
        '"""Auto-generated Streamlit CRUD app."""',
        "",
        "import sqlite3",
        "import streamlit as st",
        "import pandas as pd",
        "",
        f'DB_PATH = "{db_path}"',
        f'TABLE = "{schema.table_name}"',
        "",
        "",
        "def get_conn():",
        "    return sqlite3.connect(DB_PATH)",
        "",
        "",
        "def read_all():",
        "    conn = get_conn()",
        '    df = pd.read_sql(f"SELECT * FROM {TABLE}", conn)',
        "    conn.close()",
        "    return df",
        "",
        "",
        "def main():",
        f'    st.set_page_config(page_title="{schema.table_name} Manager")',
        f'    st.title("{schema.table_name}")',
        "",
        '    tab_view, tab_add = st.tabs(["View Data", "Add Record"])',
        "",
        "    with tab_view:",
        "        df = read_all()",
        '        st.dataframe(df, width="stretch")',
        '        st.caption(f"{len(df)} records")',
        "",
        "    with tab_add:",
    ]

    for col in schema.columns:
        if col.dtype == "text":
            lines.append(f'        {col.name} = st.text_input("{col.name}")')
        elif col.dtype in ("integer", "float"):
            lines.append(f'        {col.name} = st.number_input("{col.name}", value=0)')
        elif col.dtype == "boolean":
            lines.append(f'        {col.name} = st.checkbox("{col.name}")')
        elif col.dtype == "date":
            lines.append(f'        {col.name} = st.date_input("{col.name}")')

    col_names = ", ".join(f'"{c.name}"' for c in schema.columns)
    placeholders = ", ".join(["?"] * len(schema.columns))
    values_expr = ", ".join(c.name for c in schema.columns)

    lines.extend(
        [
            "",
            '        if st.button("Add Record"):',
            "            conn = get_conn()",
            f"            conn.execute("
            f"'INSERT INTO {schema.table_name} ({col_names}) "
            f"VALUES ({placeholders})', ({values_expr},))",
            "            conn.commit()",
            "            conn.close()",
            '            st.success("Record added.")',
            "            st.rerun()",
            "",
            "",
            'if __name__ == "__main__":',
            "    main()",
        ]
    )

    return "\n".join(lines) + "\n"


def query_db(db_path: str | Path, sql: str, params: tuple = ()) -> list[dict[str, Any]]:
    """Run a read query against a SQLite database."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(sql, params).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()
