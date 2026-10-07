"""SAP Datasphere JSON Parser service.

Parses arbitrary SAP Datasphere JSON structures (CSN, Data Builder artifacts,
Remote Tables, Views, multi-entity dumps) into clean, structured SourceTable objects.
"""

from __future__ import annotations
import json
import logging
from pathlib import Path
from typing import Any, BinaryIO, TextIO

from app.domain.source import InferredClassification, SourceField, SourceTable

logger = logging.getLogger(__name__)

DATE_TIME_TYPES = {
    "cds.date", "cds.time", "cds.datetime", "cds.timestamp",
    "date", "time", "timestamp", "seconddate", "datetime", "datetime2"
}

NUMERIC_TYPES = {
    "cds.decimal", "cds.integer", "cds.integer64", "cds.int16", "cds.int32", "cds.int64",
    "cds.uint8", "cds.double", "int", "integer", "bigint", "smallint", "tinyint",
    "decimal", "numeric", "float", "double", "real", "double precision"
}

BOOLEAN_TYPES = {
    "cds.boolean", "boolean", "bool"
}

BINARY_TYPES = {
    "cds.binary", "cds.largebinary", "blob", "varbinary", "binary", "raw", "bytea"
}


class DatasphereParser:
    """Parser for SAP Datasphere metadata JSON exports."""

    @classmethod
    def parse(
        cls, 
        source: str | bytes | dict[str, Any] | list[Any] | Path | TextIO | BinaryIO
    ) -> list[SourceTable]:
        """Parses any Datasphere JSON input into a list of SourceTable objects."""
        raw_data = cls._load_json(source)
        return cls._extract_tables(raw_data)

    @classmethod
    def _load_json(
        cls, 
        source: str | bytes | dict[str, Any] | list[Any] | Path | TextIO | BinaryIO
    ) -> Any:
        if isinstance(source, (dict, list)):
            return source
        if isinstance(source, (str, Path)):
            try:
                path = Path(source)
                if path.is_file():
                    with open(path, "r", encoding="utf-8") as f:
                        return json.load(f)
            except (OSError, ValueError):
                pass
            
            if isinstance(source, str):
                return json.loads(source)
                
        if isinstance(source, bytes):
            return json.loads(source.decode("utf-8"))
            
        if hasattr(source, "read"):
            content = source.read()
            if isinstance(content, bytes):
                content = content.decode("utf-8")
            return json.loads(content)
            
        raise ValueError(f"Unsupported source format: {type(source)}")

    @classmethod
    def _extract_tables(cls, data: Any) -> list[SourceTable]:
        tables: list[SourceTable] = []

        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    extracted = cls._parse_single_table_or_csn(item)
                    tables.extend(extracted)
            return tables

        if not isinstance(data, dict):
            return []

        # 1. Standard SAP CSN Format
        if "definitions" in data and isinstance(data["definitions"], dict):
            definitions = data["definitions"]
            for entity_name, entity_def in definitions.items():
                if isinstance(entity_def, dict):
                    kind = entity_def.get("kind", "")
                    if kind in ("entity", "type", "view", "context") or "elements" in entity_def or "columns" in entity_def:
                        table = cls._parse_csn_entity(entity_name, entity_def, root_meta=data.get("meta", {}))
                        if table:
                            tables.append(table)
            if tables:
                return tables

        # 2. Wrapped formats: {"tables": [...]}, {"entities": [...]}
        for wrapper_key in ("tables", "entities", "sources", "remoteTables", "models"):
            if wrapper_key in data and isinstance(data[wrapper_key], list):
                for item in data[wrapper_key]:
                    if isinstance(item, dict):
                        extracted = cls._parse_single_table_or_csn(item)
                        tables.extend(extracted)
                if tables:
                    return tables

        # 3. Direct single table or entity representation
        single_table = cls._parse_single_table_or_csn(data)
        if single_table:
            tables.extend(single_table)

        return tables

    @classmethod
    def _parse_single_table_or_csn(cls, item: dict[str, Any]) -> list[SourceTable]:
        if "definitions" in item and isinstance(item["definitions"], dict):
            return cls._extract_tables(item)
            
        table = cls._parse_table_dict(item)
        return [table] if table else []

    @classmethod
    def _parse_csn_entity(
        cls, 
        entity_name: str, 
        entity_def: dict[str, Any], 
        root_meta: dict[str, Any]
    ) -> SourceTable | None:
        elements = entity_def.get("elements") or entity_def.get("columns") or {}
        
        annotations: dict[str, Any] = {}
        additional_metadata: dict[str, Any] = {}
        for k, v in entity_def.items():
            if k.startswith("@"):
                annotations[k] = v
            elif k not in ("elements", "columns", "kind", "name", "label", "doc"):
                additional_metadata[k] = v

        label = (
            annotations.get("@EndUserText.label") 
            or annotations.get("@title") 
            or annotations.get("@description") 
            or entity_def.get("label")
            or entity_def.get("doc")
        )

        source_connection = (
            annotations.get("@DataWarehouse.connectionName")
            or annotations.get("@DataWarehouse.remoteConnection")
            or annotations.get("@SapEnterprise.connection")
            or entity_def.get("sourceConnection")
            or entity_def.get("connection")
        )

        remote_source = (
            annotations.get("@DataWarehouse.remoteSource")
            or annotations.get("@SapEnterprise.remoteSource")
            or entity_def.get("remoteSource")
        )

        remote_table = (
            annotations.get("@DataWarehouse.remoteTable")
            or annotations.get("@DataWarehouse.remoteEntity")
            or annotations.get("@SapEnterprise.remoteObject")
            or entity_def.get("remoteTable")
            or entity_def.get("remoteEntity")
        )

        modeling_metadata = {
            "kind": entity_def.get("kind", "entity"),
            "dataCategory": annotations.get("@Analytics.dataCategory") or annotations.get("@dataCategory"),
            "semanticUsage": annotations.get("@DataWarehouse.semanticUsage") or entity_def.get("semanticUsage"),
        }
        if root_meta:
            modeling_metadata["root_meta"] = root_meta

        capabilities = annotations.get("@DataWarehouse.capabilities", [])
        if isinstance(capabilities, dict):
            capabilities = list(capabilities.keys())
        elif not isinstance(capabilities, list):
            capabilities = [str(capabilities)] if capabilities else []

        filters = []
        if "@DataWarehouse.filter" in annotations:
            filters.append(annotations["@DataWarehouse.filter"])
        if "filters" in entity_def:
            if isinstance(entity_def["filters"], list):
                filters.extend(entity_def["filters"])
            else:
                filters.append(entity_def["filters"])

        fields: list[SourceField] = []
        if isinstance(elements, dict):
            for elem_name, elem_def in elements.items():
                if isinstance(elem_def, dict):
                    field = cls._parse_csn_field(elem_name, elem_def)
                    fields.append(field)
        elif isinstance(elements, list):
            for elem_item in elements:
                if isinstance(elem_item, dict):
                    name = elem_item.get("name") or elem_item.get("id") or "UNKNOWN_FIELD"
                    field = cls._parse_csn_field(name, elem_item)
                    fields.append(field)

        return SourceTable(
            name=entity_name,
            label=label,
            source_connection=source_connection,
            remote_source=remote_source,
            remote_table=remote_table,
            modeling_metadata={k: v for k, v in modeling_metadata.items() if v is not None},
            capabilities=capabilities,
            fields=fields,
            filters=filters,
            annotations=annotations,
            additional_metadata=additional_metadata,
        )

    @classmethod
    def _parse_csn_field(cls, name: str, field_def: dict[str, Any]) -> SourceField:
        field_annotations: dict[str, Any] = {}
        field_additional: dict[str, Any] = {}

        for k, v in field_def.items():
            if k.startswith("@"):
                field_annotations[k] = v
            elif k not in (
                "type", "length", "precision", "scale", "key", "notNull", 
                "nullable", "label", "doc", "nativeType", "filter", "filterExpression"
            ):
                field_additional[k] = v

        label = (
            field_annotations.get("@EndUserText.label")
            or field_annotations.get("@title")
            or field_annotations.get("@description")
            or field_def.get("label")
            or field_def.get("doc")
        )

        data_type = str(field_def.get("type", "cds.String"))
        native_type = field_def.get("nativeType") or field_annotations.get("@DataWarehouse.nativeType")
        length = field_def.get("length")
        precision = field_def.get("precision")
        scale = field_def.get("scale")

        is_key = bool(field_def.get("key", False) or field_annotations.get("@DataWarehouse.isKey", False))
        
        if "notNull" in field_def:
            is_nullable = not bool(field_def["notNull"])
        elif "nullable" in field_def:
            is_nullable = bool(field_def["nullable"])
        else:
            is_nullable = not is_key

        is_filterable = bool(field_annotations.get("@Analytics.Filter.filterable", True))
        filter_expr = field_def.get("filterExpression") or field_def.get("filter") or field_annotations.get("@DataWarehouse.filter")

        explicit_agg = (
            field_annotations.get("@Aggregation.default")
            or field_annotations.get("@DefaultAggregation")
            or field_def.get("aggregation")
            or field_def.get("defaultAggregation")
        )
        if explicit_agg and isinstance(explicit_agg, str):
            explicit_agg = explicit_agg.replace("#", "").strip()

        inferred = cls._infer_field_classification(
            name=name,
            data_type=data_type,
            native_type=native_type,
            is_key=is_key,
            annotations=field_annotations,
        )

        return SourceField(
            name=name,
            label=label,
            data_type=data_type,
            native_type=native_type,
            length=int(length) if length is not None else None,
            precision=int(precision) if precision is not None else None,
            scale=int(scale) if scale is not None else None,
            is_key=is_key,
            is_nullable=is_nullable,
            is_filterable=is_filterable,
            filter_expression=filter_expr,
            explicit_aggregation=explicit_agg,
            inferred_classification=inferred,
            annotations=field_annotations,
            additional_metadata=field_additional,
        )

    @classmethod
    def _parse_table_dict(cls, data: dict[str, Any]) -> SourceTable | None:
        name = (
            data.get("name") 
            or data.get("entityName") 
            or data.get("tableName") 
            or data.get("id")
            or data.get("technicalName")
            or "UNNAMED_TABLE"
        )

        label = data.get("label") or data.get("description") or data.get("title")

        source_info = data.get("source", {}) if isinstance(data.get("source"), dict) else {}
        source_connection = (
            data.get("sourceConnection") 
            or data.get("connectionName") 
            or data.get("connection") 
            or source_info.get("connection")
            or source_info.get("connectionName")
        )
        remote_source = (
            data.get("remoteSource") 
            or data.get("remoteSourceName") 
            or source_info.get("remoteSource")
        )
        remote_table = (
            data.get("remoteTable") 
            or data.get("remoteTableName") 
            or data.get("remoteEntity") 
            or source_info.get("remoteObject")
            or source_info.get("remoteEntity")
            or source_info.get("remoteTable")
        )

        raw_fields = data.get("fields") or data.get("columns") or data.get("elements") or []
        fields: list[SourceField] = []

        if isinstance(raw_fields, list):
            for col in raw_fields:
                if isinstance(col, dict):
                    fields.append(cls._parse_generic_field_dict(col))
        elif isinstance(raw_fields, dict):
            for col_name, col_def in raw_fields.items():
                if isinstance(col_def, dict):
                    col_dict = {"name": col_name, **col_def}
                    fields.append(cls._parse_generic_field_dict(col_dict))

        annotations: dict[str, Any] = {}
        additional_metadata: dict[str, Any] = {}
        for k, v in data.items():
            if k.startswith("@"):
                annotations[k] = v
            elif k not in (
                "name", "entityName", "tableName", "id", "technicalName", "label", "description",
                "title", "source", "sourceConnection", "connectionName", "connection",
                "remoteSource", "remoteSourceName", "remoteTable", "remoteTableName", "remoteEntity",
                "fields", "columns", "elements", "capabilities", "filters", "modeling"
            ):
                additional_metadata[k] = v

        capabilities = data.get("capabilities", [])
        if isinstance(capabilities, dict):
            capabilities = list(capabilities.keys())
        elif not isinstance(capabilities, list):
            capabilities = [str(capabilities)] if capabilities else []

        filters = data.get("filters", [])
        if not isinstance(filters, list):
            filters = [filters] if filters else []

        modeling_metadata = data.get("modeling", {})
        if not isinstance(modeling_metadata, dict):
            modeling_metadata = {"raw": modeling_metadata}

        return SourceTable(
            name=name,
            label=label,
            source_connection=source_connection,
            remote_source=remote_source,
            remote_table=remote_table,
            modeling_metadata=modeling_metadata,
            capabilities=capabilities,
            fields=fields,
            filters=filters,
            annotations=annotations,
            additional_metadata=additional_metadata,
        )

    @classmethod
    def _parse_generic_field_dict(cls, col: dict[str, Any]) -> SourceField:
        name = col.get("name") or col.get("id") or col.get("columnName") or col.get("technicalName") or "FIELD"
        label = col.get("label") or col.get("title") or col.get("description")
        
        data_type = str(col.get("dataType") or col.get("type") or "cds.String")
        native_type = col.get("nativeDataType") or col.get("nativeType")
        length = col.get("length") or col.get("maxLength")
        precision = col.get("precision")
        scale = col.get("scale")

        is_key = bool(col.get("isKey") or col.get("key") or col.get("primaryKey", False))
        
        if "nullable" in col:
            is_nullable = bool(col["nullable"])
        elif "isNullable" in col:
            is_nullable = bool(col["isNullable"])
        elif "notNull" in col:
            is_nullable = not bool(col["notNull"])
        else:
            is_nullable = not is_key

        is_filterable = bool(col.get("filterable", col.get("isFilterable", True)))
        filter_expr = col.get("filterExpression") or col.get("filter")

        explicit_agg = col.get("aggregation") or col.get("defaultAggregation") or col.get("aggregationType")
        if explicit_agg and isinstance(explicit_agg, str):
            explicit_agg = explicit_agg.replace("#", "").strip()

        annotations: dict[str, Any] = {}
        additional: dict[str, Any] = {}
        for k, v in col.items():
            if k.startswith("@"):
                annotations[k] = v
            elif k not in (
                "name", "id", "columnName", "technicalName", "label", "title", "description",
                "dataType", "type", "nativeDataType", "nativeType", "length", "maxLength",
                "precision", "scale", "isKey", "key", "primaryKey", "nullable", "isNullable",
                "notNull", "filterable", "isFilterable", "filterExpression", "filter",
                "aggregation", "defaultAggregation", "aggregationType"
            ):
                additional[k] = v

        inferred = cls._infer_field_classification(
            name=name,
            data_type=data_type,
            native_type=native_type,
            is_key=is_key,
            annotations=annotations,
        )

        return SourceField(
            name=name,
            label=label,
            data_type=data_type,
            native_type=native_type,
            length=int(length) if length is not None else None,
            precision=int(precision) if precision is not None else None,
            scale=int(scale) if scale is not None else None,
            is_key=is_key,
            is_nullable=is_nullable,
            is_filterable=is_filterable,
            filter_expression=filter_expr,
            explicit_aggregation=explicit_agg,
            inferred_classification=inferred,
            annotations=annotations,
            additional_metadata=additional,
        )

    @classmethod
    def _infer_field_classification(
        cls,
        name: str,
        data_type: str,
        native_type: str | None,
        is_key: bool,
        annotations: dict[str, Any]
    ) -> InferredClassification:
        if annotations.get("@Analytics.Measure") is True:
            return InferredClassification.MEASURE_CANDIDATE
        if annotations.get("@Analytics.Dimension") is True:
            return InferredClassification.DIMENSION_CANDIDATE

        norm_type = data_type.lower().strip()
        norm_native = (native_type or "").lower().strip()
        norm_name = name.upper().strip()

        if is_key:
            return InferredClassification.KEY_IDENTIFIER

        if norm_type in BOOLEAN_TYPES or norm_native in BOOLEAN_TYPES:
            return InferredClassification.BOOLEAN_FLAG

        if norm_type in BINARY_TYPES or norm_native in BINARY_TYPES:
            return InferredClassification.BINARY_OR_BLOB

        if norm_type in DATE_TIME_TYPES or norm_native in DATE_TIME_TYPES:
            return InferredClassification.DATE_TIME

        if norm_type in NUMERIC_TYPES or norm_native in NUMERIC_TYPES:
            if any(suffix in norm_name for suffix in ("_ID", "ID", "_KEY", "_CODE", "_NUM", "_NO", "YEAR", "ZIP")):
                return InferredClassification.DIMENSION_CANDIDATE
            return InferredClassification.MEASURE_CANDIDATE

        if any(token in norm_type for token in ("string", "char", "text", "varchar", "nvarchar")):
            if norm_name.endswith(("_ID", "_KEY", "_UUID", "_GUID", "_NR", "_NO")):
                return InferredClassification.KEY_IDENTIFIER
            return InferredClassification.DIMENSION_CANDIDATE

        return InferredClassification.DIMENSION_CANDIDATE


def parse_datasphere_json(
    source: str | bytes | dict[str, Any] | list[Any] | Path | TextIO | BinaryIO
) -> list[SourceTable]:
    """Helper function to parse Datasphere source metadata."""
    return DatasphereParser.parse(source)
