import duckdb
from pathlib import Path
from datetime import datetime


def sql_quote(value: str) -> str:
    return value.replace("'", "''")


def safe_table_name(name: str) -> str:
    return name.replace('"', '""')


def json_to_parquet_and_duckdb():
    input_path = input("Enter path to JSON file or JSON directory: ").strip()
    output_dir = input("Enter directory where Parquet and DuckDB should be created: ").strip()
    table_name = input("Enter DuckDB table name [data_table]: ").strip() or "data_table"

    input_path = Path(input_path).expanduser().resolve()
    output_dir = Path(output_dir).expanduser().resolve()

    if not input_path.exists():
        raise FileNotFoundError(f"Input path does not exist: {input_path}")

    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    parquet_file = output_dir / f"data_{timestamp}.parquet"
    duckdb_file = output_dir / f"data_{timestamp}.duckdb"

    if input_path.is_dir():
        json_source = str(input_path / "*.json")
    else:
        json_source = str(input_path)

    safe_table = safe_table_name(table_name)

    con = duckdb.connect(str(duckdb_file))
    con.execute("PRAGMA threads=1")

    print("Converting JSON to Parquet...")

    con.execute(f"""
        COPY (
            SELECT *
            FROM read_json_auto(
                '{sql_quote(json_source)}',
                maximum_object_size = 100000000
            )
        )
        TO '{sql_quote(str(parquet_file))}'
        (
            FORMAT PARQUET,
            COMPRESSION ZSTD
        );
    """)

    print("Creating DuckDB table from Parquet...")

    con.execute(f'DROP TABLE IF EXISTS "{safe_table}"')

    con.execute(f"""
        CREATE TABLE "{safe_table}" AS
        SELECT *
        FROM read_parquet('{sql_quote(str(parquet_file))}')
    """)

    con.close()

    print()
    print("Created Parquet file:")
    print(parquet_file)

    print()
    print("Created DuckDB file:")
    print(duckdb_file)

    print()
    print("Open this DuckDB file in DBeaver:")
    print(duckdb_file)

    print()
    print("Then query:")
    print(f'SELECT * FROM "{table_name}" LIMIT 100;')


if __name__ == "__main__":
    json_to_parquet_and_duckdb()