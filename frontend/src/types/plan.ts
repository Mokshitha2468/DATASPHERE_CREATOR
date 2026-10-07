export interface ColumnDecision {
  name: string;
  reason: string;
}

export interface FilterSpec {
  column: string;
  operator: string;
  values: any[];
  reason: string;
}

export interface PlanSpec {
  fact_view_name: string;
  source_table: string;
  selected_columns: ColumnDecision[];
  dropped_columns: ColumnDecision[];
  filters: FilterSpec[];
  unsupported: string[];
  summary: string;
}

export interface PlanVersion {
  version: number;
  plan: PlanSpec;
  created_at: string;
  source: string;
}
