"""Unit tests for sample data pattern learning and privacy enforcement."""

import json
from app.services.sample_rows import parse_and_learn_patterns


def test_sample_rows_csv_pattern_learning():
    csv_text = (
        "EMPLOYEE_ID,COUNTRY,START_DATE,IS_MANAGER,SALARY\n"
        "EMP_001,US,20210101,Y,100000\n"
        "EMP_002,DE,20210615,N,85000\n"
        "EMP_003,FR,20220301,Y,110000\n"
    )

    patterns = parse_and_learn_patterns(csv_text)
    
    # 1. Prefix learning
    assert "EMPLOYEE_ID" in patterns.columns
    assert patterns.columns["EMPLOYEE_ID"].prefix == "EMP_"

    # 2. Date format learning
    assert "START_DATE" in patterns.columns
    assert patterns.columns["START_DATE"].date_format == "YYYYMMDD"

    # 3. Flag learning
    assert "IS_MANAGER" in patterns.columns
    assert set(patterns.columns["IS_MANAGER"].flag_values) == {"Y", "N"}

    # 4. Numeric learning
    assert "SALARY" in patterns.columns
    assert patterns.columns["SALARY"].is_numeric is True
    assert patterns.columns["SALARY"].numeric_min == 85000.0


def test_sample_rows_json_pattern_learning():
    json_data = [
        {"CODE": "CUST_A", "STATUS": "X", "DATE": "2024-01-10"},
        {"CODE": "CUST_B", "STATUS": "X", "DATE": "2024-05-20"},
    ]
    json_str = json.dumps(json_data)
    patterns = parse_and_learn_patterns(json_str)

    assert patterns.columns["CODE"].prefix == "CUST_"
    assert patterns.columns["DATE"].date_format == "YYYY-MM-DD"


def test_sample_rows_cap_at_20_rows():
    # 30 rows generated
    lines = ["ID,VAL"] + [f"ID_{i},{i*10}" for i in range(30)]
    csv_data = "\n".join(lines)
    patterns = parse_and_learn_patterns(csv_data, max_rows=20)

    # Patterns extracted successfully
    assert patterns.columns["ID"].prefix == "ID_"
    # Ensure real_row_hashes capped at 20
    assert len(patterns.real_row_hashes) == 20
