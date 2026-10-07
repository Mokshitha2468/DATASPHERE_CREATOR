"""Source domain models for SAP Datasphere metadata representation."""

from __future__ import annotations
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class InferredClassification(str, Enum):
    """Inferred semantic classification by Python analysis."""
    KEY_IDENTIFIER = "KEY_IDENTIFIER"
    DIMENSION_CANDIDATE = "DIMENSION_CANDIDATE"
    MEASURE_CANDIDATE = "MEASURE_CANDIDATE"
    DATE_TIME = "DATE_TIME"
    BOOLEAN_FLAG = "BOOLEAN_FLAG"
    BINARY_OR_BLOB = "BINARY_OR_BLOB"
    UNKNOWN = "UNKNOWN"


class SourceField(BaseModel):
    """Represents a single field/column extracted from a SAP Datasphere source."""
    
    name: str = Field(description="Column/element name in the Datasphere definition")
    label: str | None = Field(default=None, description="Human readable label/title if defined")
    
    # Type metadata
    data_type: str = Field(default="cds.String", description="Datasphere/CSN or standard data type")
    native_type: str | None = Field(default=None, description="Native database/remote data type if provided")
    length: int | None = Field(default=None, description="Length for string/char/binary types")
    precision: int | None = Field(default=None, description="Precision for numeric/decimal types")
    scale: int | None = Field(default=None, description="Scale for decimal/floating point types")
    
    # Constraints & Capabilities
    is_key: bool = Field(default=False, description="Whether this column is marked as a primary/entity key")
    is_nullable: bool = Field(default=True, description="Whether null values are permitted")
    is_filterable: bool = Field(default=True, description="Whether column supports filtering")
    filter_expression: str | dict[str, Any] | None = Field(
        default=None, 
        description="Explicit filter expression defined in source metadata"
    )
    
    # Explicit aggregation from source metadata (NOT invented)
    explicit_aggregation: str | None = Field(
        default=None, 
        description="Explicit aggregation type (e.g. SUM, COUNT, MAX) ONLY if present in source metadata"
    )
    
    # Inferred classification
    inferred_classification: InferredClassification = Field(
        default=InferredClassification.UNKNOWN,
        description="Python-inferred classification for downstream modeling"
    )
    
    # Metadata preservation
    annotations: dict[str, Any] = Field(default_factory=dict, description="CSN/@ annotations present on this field")
    additional_metadata: dict[str, Any] = Field(default_factory=dict, description="Preserved unparsed or custom attributes")

    def to_llm_dict(self) -> dict[str, Any]:
        """Returns a clean representation suitable for LLM prompt ingestion."""
        res: dict[str, Any] = {
            "name": self.name,
            "data_type": self.data_type,
            "is_key": self.is_key,
            "inferred_classification": self.inferred_classification.value,
        }
        if self.label:
            res["label"] = self.label
        if self.native_type:
            res["native_type"] = self.native_type
        if self.length is not None:
            res["length"] = self.length
        if self.precision is not None:
            res["precision"] = self.precision
        if self.scale is not None:
            res["scale"] = self.scale
        if not self.is_nullable:
            res["not_null"] = True
        if self.explicit_aggregation:
            res["explicit_aggregation"] = self.explicit_aggregation
        if self.filter_expression:
            res["filter_expression"] = self.filter_expression
        return res


class SourceTable(BaseModel):
    """Represents what Python understands about one SAP Datasphere source table/entity."""
    
    name: str = Field(description="Technical name of the entity / table in Datasphere")
    label: str | None = Field(default=None, description="Human readable label of the entity")
    
    # Connection & Remote Source info
    source_connection: str | None = Field(default=None, description="Connection name (e.g. S4HANA_CONN, HANA_CLOUD)")
    remote_source: str | None = Field(default=None, description="Remote source name if applicable")
    remote_table: str | None = Field(default=None, description="Remote table/entity name in underlying system")
    
    # Modeling & Capabilities
    modeling_metadata: dict[str, Any] = Field(
        default_factory=dict, 
        description="Semantic usage, data category, CSN kind, etc."
    )
    capabilities: list[str] | dict[str, Any] = Field(
        default_factory=list, 
        description="Source capabilities e.g. deltaLoad, fullLoad, filterable"
    )
    
    # Fields
    fields: list[SourceField] = Field(default_factory=list, description="List of columns/fields in this table")
    
    # Source-level filter expressions
    filters: list[Any] = Field(default_factory=list, description="Explicit source filters defined on the entity")
    
    # Annotations & Metadata preservation
    annotations: dict[str, Any] = Field(default_factory=dict, description="Entity-level annotations")
    additional_metadata: dict[str, Any] = Field(default_factory=dict, description="Unrecognized or raw source attributes")

    def get_columns(self) -> list[str]:
        """Returns the names of all fields in the table."""
        return [f.name for f in self.fields]

    def get_key_columns(self) -> list[str]:
        """Returns the names of all primary/key fields."""
        return [f.name for f in self.fields if f.is_key]

    def get_filterable_columns(self) -> list[str]:
        """Returns the names of all filterable fields."""
        return [f.name for f in self.fields if f.is_filterable]

    def get_dimensions(self) -> list[SourceField]:
        """Returns fields classified or explicitly marked as dimensions."""
        dim_classes = {
            InferredClassification.DIMENSION_CANDIDATE,
            InferredClassification.DATE_TIME,
            InferredClassification.BOOLEAN_FLAG,
            InferredClassification.KEY_IDENTIFIER,
        }
        return [
            f for f in self.fields 
            if f.inferred_classification in dim_classes or (
                f.annotations.get("@Analytics.Dimension") is True or
                f.annotations.get("@ObjectModel.foreignKey.association") is not None
            )
        ]

    def get_measures(self) -> list[SourceField]:
        """Returns fields classified or explicitly marked as numeric measures."""
        return [
            f for f in self.fields 
            if f.inferred_classification == InferredClassification.MEASURE_CANDIDATE or
            f.explicit_aggregation is not None or
            f.annotations.get("@Analytics.Measure") is True or
            f.annotations.get("@DefaultAggregation") is not None
        ]

    def get_field(self, name: str) -> SourceField | None:
        """Retrieves a field by name (case-insensitive fallback)."""
        for f in self.fields:
            if f.name == name:
                return f
        name_lower = name.lower()
        for f in self.fields:
            if f.name.lower() == name_lower:
                return f
        return None

    def to_llm_summary(self) -> dict[str, Any]:
        """Produces a clean structured summary tailored for LLM reasoning."""
        return {
            "name": self.name,
            "label": self.label or self.name,
            "source_connection": self.source_connection,
            "remote_table": self.remote_table,
            "key_columns": self.get_key_columns(),
            "fields": [f.to_llm_dict() for f in self.fields],
            "dimension_count": len(self.get_dimensions()),
            "measure_count": len(self.get_measures()),
            "modeling_metadata": self.modeling_metadata,
            "capabilities": self.capabilities,
        }
