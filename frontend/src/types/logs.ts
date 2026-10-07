export interface AgentLogEvent {
  type: string;
  agent?: string;
  step?: string;
  input?: any;
  output?: any;
  error?: string;
  status?: string;
  duration_ms?: number;
  timestamp: number;
  iso_time: string;
  message?: string;
}
