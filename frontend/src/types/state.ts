import { SourceTable } from './source';
import { PlanSpec, PlanVersion } from './plan';

export interface SharedState {
  intention?: string | null;
  requirement?: string | null;
  source_tables: SourceTable[];
  dummy_data: Record<string, Record<string, any>[]>;
  plan?: PlanSpec | null;
  plan_version: number;
  plan_versions: PlanVersion[];
  plan_status: 'draft' | 'approved' | 'stale';
  fact_view_name?: string | null;
  stage: 'source' | 'plan' | 'fact_view' | 'graphical_view' | 'analytical_model';
  fact_view_json?: Record<string, any> | null;
  graphical_view_json?: Record<string, any> | null;
  analytical_model_json?: Record<string, any> | null;
  llm_mode: 'MOCK' | 'REAL';
  errors: string[];
  logs: string[];
}
