"""Tests for Excel-to-web converter module."""

import tempfile

import pandas as pd

from scrape_and_serve.excel_converter import (
    create_sqlite_db,
    detect_column_dtype,
    detect_schema,
    generate_streamlit_code,
    query_db,
    read_excel,
)


def _sample_df():
    return pd.DataFrame({
        "name": ["Alice", "Bob", "Charlie"],
        "age": [30, 25, 35],
        "salary": [50000.0, 60000.0, 70000.0],
        "active": [True, False, True],
    })


class TestDetectColumnDtype:
    def test_integer(self):
        s = pd.Series([1, 2, 3])
        assert detect_column_dtype(s) == "integer"

    def test_float(self):
        s = pd.Series([1.1, 2.2, 3.3])
        assert detect_column_dtype(s) == "float"

    def test_boolean(self):
        s = pd.Series([True, False, True])
        assert detect_column_dtype(s) == "boolean"

    def test_text(self):
        s = pd.Series(["a", "b", "c"])
        assert detect_column_dtype(s) == "text"

    def test_datetime(self):
        s = pd.Series(pd.to_datetime(["2024-01-01", "2024-02-01"]))
        assert detect_column_dtype(s) == "date"


class TestDetectSchema:
    def test_basic(self):
        df = _sample_df()
        schema = detect_schema(df, "employees")
        assert schema.table_name == "employees"
        assert schema.row_count == 3
        assert len(schema.columns) == 4
        names = [c.name for c in schema.columns]
        assert "name" in names
        assert "age" in names

    def test_column_types(self):
        df = _sample_df()
        schema = detect_schema(df)
        type_map = {c.name: c.dtype for c in schema.columns}
        assert type_map["name"] == "text"
        assert type_map["age"] == "integer"
        assert type_map["salary"] == "float"
        assert type_map["active"] == "boolean"

    def test_sample_values(self):
        df = _sample_df()
        schema = detect_schema(df)
        name_col = [c for c in schema.columns if c.name == "name"][0]
        assert len(name_col.sample_values) <= 3
        assert "Alice" in name_col.sample_values


class TestReadExcel:
    def test_read_csv(self):
        with tempfile.NamedTemporaryFile(suffix=".csv", mode="w", delete=False) as f:
            f.write("a,b\n1,2\n3,4\n")
            f.flush()
            sheets = read_excel(f.name)
        assert "Sheet1" in sheets
        assert len(sheets["Sheet1"]) == 2

    def test_read_xlsx(self):
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            df = _sample_df()
            df.to_excel(f.name, index=False)
            sheets = read_excel(f.name)
        assert "Sheet1" in sheets
        assert len(sheets["Sheet1"]) == 3


class TestCreateSqliteDb:
    def test_create_and_query(self):
        df = _sample_df()
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        schema = create_sqlite_db(df, "employees", db_path)
        assert schema.table_name == "employees"

        rows = query_db(db_path, "SELECT * FROM employees")
        assert len(rows) == 3
        assert rows[0]["name"] == "Alice"

    def test_id_column(self):
        df = _sample_df()
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        create_sqlite_db(df, "test", db_path)
        rows = query_db(db_path, "SELECT id FROM test")
        ids = [r["id"] for r in rows]
        assert ids == [1, 2, 3]


class TestGenerateStreamlitCode:
    def test_generates_valid_python(self):
        df = _sample_df()
        schema = detect_schema(df, "employees")
        code = generate_streamlit_code(schema)
        assert "import streamlit" in code
        assert "employees" in code
        assert "def main()" in code

    def test_includes_columns(self):
        df = _sample_df()
        schema = detect_schema(df, "people")
        code = generate_streamlit_code(schema)
        assert "name" in code
        assert "age" in code


class TestQueryDb:
    def test_with_params(self):
        df = _sample_df()
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        create_sqlite_db(df, "emp", db_path)
        rows = query_db(db_path, "SELECT * FROM emp WHERE name = ?", ("Bob",))
        assert len(rows) == 1
        assert rows[0]["name"] == "Bob"
