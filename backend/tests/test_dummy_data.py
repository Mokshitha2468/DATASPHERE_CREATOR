"""Unit tests for Dummy Data Generator in Phase 2."""

from pathlib import Path
import datetime
from app.domain.source import SourceField, SourceTable, InferredClassification
from app.services.dummy_data import generate_dummy_data, DummyDataGenerator
from app.services.sample_rows import parse_and_learn_patterns
from app.services.source_parser import parse_datasphere_json

SAMPLE_DIR = Path(__file__).parent / "sample_data"


def test_dummy_data_row_count_and_keys():
    csn_file = SAMPLE_DIR / "sales_order_csn.json"
    tables = parse_datasphere_json(csn_file)
    table = tables[0]

    rows = generate_dummy_data(table, row_count=20)
    assert len(rows) == 20

    cols = set(table.get_columns())
    for r in rows:
        assert set(r.keys()) == cols

    # Key combination uniqueness across all 20 rows
    key_tuples = [(r["SALES_ORDER_ID"], r["ITEM_NO"]) for r in rows]
    assert len(set(key_tuples)) == 20


def test_dummy_data_determinism():
    rt_file = SAMPLE_DIR / "customer_remote_table.json"
    tables = parse_datasphere_json(rt_file)
    table = tables[0]

    run1 = generate_dummy_data(table, row_count=20, seed=42)
    run2 = generate_dummy_data(table, row_count=20, seed=42)
    assert run1 == run2


def test_dummy_data_constraints():
    table = SourceTable(
        name="CONSTRAINTS_TEST",
        fields=[
            SourceField(name="CODE", data_type="cds.String", length=5, is_key=True),
            SourceField(name="COUNTRY", data_type="cds.String", length=2),
            SourceField(name="AMOUNT", data_type="cds.Decimal", precision=8, scale=2),
            SourceField(name="START_DATE", data_type="cds.Date", label="Start Date"),
            SourceField(name="END_DATE", data_type="cds.Date", label="End Date"),
            SourceField(name="IS_VALID", data_type="cds.Boolean"),
        ]
    )

    rows = generate_dummy_data(table, row_count=20)
    assert len(rows) == 20

    for r in rows:
        assert len(str(r["CODE"])) <= 5
        assert len(str(r["COUNTRY"])) <= 2
        assert isinstance(r["AMOUNT"], (int, float))
        assert isinstance(r["IS_VALID"], bool)
        
        # Test valid dates and end_date >= start_date
        d_start = datetime.date.fromisoformat(r["START_DATE"]) if "-" in r["START_DATE"] else datetime.datetime.strptime(r["START_DATE"], "%Y%m%d").date()
        d_end = datetime.date.fromisoformat(r["END_DATE"]) if "-" in r["END_DATE"] else datetime.datetime.strptime(r["END_DATE"], "%Y%m%d").date()
        assert d_end >= d_start


def test_sample_data_pattern_learning_and_row_difference():
    # Real sample CSV content with prefix EMP_ and YYYYMMDD
    sample_csv = (
        "EMP_ID,FIRST_NAME,HIRE_DATE,FLAG\n"
        "EMP_101,John,20220101,Y\n"
        "EMP_102,Jane,20220201,N\n"
    )
    
    table = SourceTable(
        name="EMPLOYEES",
        fields=[
            SourceField(name="EMP_ID", data_type="cds.String", length=10, is_key=True),
            SourceField(name="FIRST_NAME", data_type="cds.String", length=30),
            SourceField(name="HIRE_DATE", data_type="cds.String", length=8),
            SourceField(name="FLAG", data_type="cds.String", length=1),
        ]
    )

    patterns = parse_and_learn_patterns(sample_csv)
    assert "EMP_ID" in patterns.columns
    assert patterns.columns["EMP_ID"].prefix == "EMP_"
    assert patterns.columns["HIRE_DATE"].date_format == "YYYYMMDD"

    # Generate synthetic rows
    rows = generate_dummy_data(table, row_count=20, patterns=patterns)
    assert len(rows) == 20

    # Ensure synthetic rows use learned prefix
    assert all(r["EMP_ID"].startswith("EMP_") for r in rows)
    # Ensure synthetic rows use learned date format
    assert all(len(r["HIRE_DATE"]) == 8 and r["HIRE_DATE"].isdigit() for r in rows)
    # Ensure unique keys
    assert len({r["EMP_ID"] for r in rows}) == 20

    # Ensure generated rows DO NOT EQUAL real sample rows
    real_rows = [
        {"EMP_ID": "EMP_101", "FIRST_NAME": "John", "HIRE_DATE": "20220101", "FLAG": "Y"},
        {"EMP_ID": "EMP_102", "FIRST_NAME": "Jane", "HIRE_DATE": "20220201", "FLAG": "N"},
    ]
    for syn_row in rows:
        for real_row in real_rows:
            assert syn_row != real_row
