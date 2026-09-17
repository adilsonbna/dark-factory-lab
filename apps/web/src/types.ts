export interface IncidentItem {
  id: string;
  title: string;
  status: string;
  severity: string;
  affected_service: string;
  detected_at: string;
  hypothesis?: string;
  root_cause?: string;
  remediation_pr_url?: string;
  remediation_diff?: string;
  retry_count: number;
  agent_timeline: Array<{ timestamp: string; agent: string; action: string }>;
  tool_calls: Array<{ tool: string; args: any; status: string }>;
  audit_trail: Array<{ event: string; timestamp: string; actor: string; reason?: string }>;
}

export interface DevOpsViewData {
  kill_switch_active: boolean;
  active_incidents: IncidentItem[];
  resolved_incidents: IncidentItem[];
  recent_telemetry_summary: { status: string; table_count: number };
}

export interface ManagementViewData {
  overall_health: string;
  open_incidents_count: number;
  resolved_incidents_count: number;
  mean_detection_seconds: number;
  mean_diagnosis_seconds: number;
  mean_recovery_seconds: number;
  mean_rollback_seconds: number;
  remediation_success_rate_percent: number;
  false_alert_rate_percent: number;
  failed_remediation_rate_percent: number;
  llm_usage_total_tokens: number;
  llm_estimated_cost_usd: number;
  release_qualification_status: string;
}
