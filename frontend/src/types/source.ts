export type InferredClassification = 
  | 'KEY_IDENTIFIER'
  | 'DIMENSION_CANDIDATE'
  | 'MEASURE_CANDIDATE'
  | 'DATE_TIME'
  | 'BOOLEAN_FLAG'
  | 'BINARY_OR_BLOB'
  | 'UNKNOWN';

export interface SourceField {
  name: string;
  label?: string | null;
  data_type: string;
  native_type?: string | null;
  length?: number | null;
  precision?: number | null;
  scale?: number | null;
  is_key: boolean;
  is_nullable: boolean;
  is_filterable: boolean;
  filter_expression?: string | Record<string, any> | null;
  explicit_aggregation?: string | null;
  inferred_classification: InferredClassification;
  annotations: Record<string, any>;
  additional_metadata: Record<string, any>;
}

export interface SourceTable {
  name: string;
  label?: string | null;
  source_connection?: string | null;
  remote_source?: string | null;
  remote_table?: string | null;
  modeling_metadata: Record<string, any>;
  capabilities: string[] | Record<string, any>;
  fields: SourceField[];
  filters: any[];
  annotations: Record<string, any>;
  additional_metadata: Record<string, any>;
}
