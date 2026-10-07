"""Unit tests for DatasphereParser and SourceTable models in Phase 2."""

from pathlib import Path
import pytest

from app.domain.source import InferredClassification, SourceField, SourceTable
from app.services.source_parser import DatasphereParser, parse_datasphere_json

SAMPLE_DIR = Path(__file__).parent / "sample_data"


def test_parse_sales_order_csn():
    csn_file = SAMPLE_DIR / "sales_order_csn.json"
    tables = parse_datasphere_json(csn_file)

    assert len(tables) == 1
    table = tables[0]
    assert table.name == "SALES_ORDERS"
    assert table.label == "Sales Orders Header & Item"
    assert table.source_connection == "S4HANA_PRD"
    assert table.remote_source == "S4HANA_REMOTE_SRC"
    assert table.remote_table == "VBAK_VBAP"
    assert "deltaLoad" in table.capabilities
    assert "STATUS <> 'DELETED'" in table.filters

    # Helper methods verification
    columns = table.get_columns()
    assert "SALES_ORDER_ID" in columns
    assert "NET_AMOUNT" in columns
    assert len(columns) == 9

    key_cols = table.get_key_columns()
    assert key_cols == ["SALES_ORDER_ID", "ITEM_NO"]

    filterable_cols = table.get_filterable_columns()
    assert len(filterable_cols) == 9

    # Check explicit aggregation vs inferred
    net_amt = table.get_field("NET_AMOUNT")
    assert net_amt is not None
    assert net_amt.data_type == "cds.Decimal"
    assert net_amt.precision == 15
    assert net_amt.scale == 2
    assert net_amt.explicit_aggregation == "SUM"
    assert net_amt.inferred_classification == InferredClassification.MEASURE_CANDIDATE

    tax_amt = table.get_field("TAX_AMOUNT")
    assert tax_amt is not None
    assert tax_amt.data_type == "cds.Decimal"
    assert tax_amt.explicit_aggregation is None
    assert tax_amt.inferred_classification == InferredClassification.MEASURE_CANDIDATE

    # Dimensions & Measures
    dims = table.get_dimensions()
    dim_names = [d.name for d in dims]
    assert "SALES_ORDER_ID" in dim_names
    assert "CUSTOMER_ID" in dim_names
    assert "ORDER_DATE" in dim_names
    assert "ORDER_STATUS" in dim_names
    assert "IS_ACTIVE" in dim_names

    measures = table.get_measures()
    measure_names = [m.name for m in measures]
    assert "NET_AMOUNT" in measure_names
    assert "TAX_AMOUNT" in measure_names

    assert table.get_field("net_amount") is net_amt


def test_parse_remote_table():
    rt_file = SAMPLE_DIR / "customer_remote_table.json"
    tables = parse_datasphere_json(rt_file)

    assert len(tables) == 1
    table = tables[0]
    assert table.name == "CUSTOMER_MASTER"
    assert table.label == "Customer Master Dimension"
    assert table.source_connection == "S4HANA_PRD"
    assert table.remote_table == "KNA1"
    assert table.get_key_columns() == ["CUSTOMER_ID"]

    c_id = table.get_field("CUSTOMER_ID")
    assert c_id is not None
    assert c_id.is_key is True
    assert c_id.is_nullable is False
    assert c_id.length == 10
    assert c_id.inferred_classification == InferredClassification.KEY_IDENTIFIER

    credit = table.get_field("CREDIT_LIMIT")
    assert credit is not None
    assert credit.precision == 12
    assert credit.scale == 2
    assert credit.inferred_classification == InferredClassification.MEASURE_CANDIDATE


def test_parse_multi_entity_csn():
    multi_file = SAMPLE_DIR / "multi_table_csn.json"
    tables = parse_datasphere_json(multi_file)

    assert len(tables) == 2
    table_names = [t.name for t in tables]
    assert "PRODUCTS" in table_names
    assert "PLANTS" in table_names


def test_additional_metadata_preservation():
    raw_json = {
        "name": "CUSTOM_SOURCE",
        "customEngineProp": "special_val_99",
        "nestedConfig": {"mode": "fast"},
        "columns": [
            {
                "name": "COL1",
                "dataType": "VARCHAR",
                "length": 20,
                "customFieldProp": 42
            }
        ]
    }
    tables = parse_datasphere_json(raw_json)
    assert len(tables) == 1
    table = tables[0]
    assert table.additional_metadata.get("customEngineProp") == "special_val_99"
    assert table.additional_metadata.get("nestedConfig") == {"mode": "fast"}
    
    col1 = table.get_field("COL1")
    assert col1 is not None
    assert col1.additional_metadata.get("customFieldProp") == 42


def test_large_schema_parsing():
    columns = []
    for i in range(150):
        columns.append({
            "name": f"COL_{i:03d}",
            "dataType": "DECIMAL" if i % 2 == 0 else "NVARCHAR",
            "length": 50 if i % 2 != 0 else None,
            "precision": 10 if i % 2 == 0 else None,
            "scale": 2 if i % 2 == 0 else None,
            "isKey": i == 0,
        })

    payload = {
        "name": "LARGE_TABLE",
        "columns": columns
    }
    tables = parse_datasphere_json(payload)
    assert len(tables) == 1
    table = tables[0]
    assert len(table.fields) == 150
    assert table.get_key_columns() == ["COL_000"]


def test_to_llm_summary():
    csn_file = SAMPLE_DIR / "sales_order_csn.json"
    tables = parse_datasphere_json(csn_file)
    summary = tables[0].to_llm_summary()

    assert summary["name"] == "SALES_ORDERS"
    assert summary["key_columns"] == ["SALES_ORDER_ID", "ITEM_NO"]
    assert len(summary["fields"]) == 9
