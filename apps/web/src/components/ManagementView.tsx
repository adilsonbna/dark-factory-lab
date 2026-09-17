import React from 'react';
import { ManagementViewData } from '../types';

interface ManagementViewProps {
  data: ManagementViewData | null;
}

export const ManagementView: React.FC<ManagementViewProps> = ({ data }) => {
  if (!data) return <div style={{ padding: '24px', color: '#94a3b8' }}>Loading Management Data...</div>;

  const kpis = [
    { label: 'Overall System Health', value: data.overall_health, color: data.overall_health === 'HEALTHY' ? '#22c55e' : '#eab308' },
    { label: 'Mean Detection Time (MTTD)', value: `${data.mean_detection_seconds}s`, color: '#38bdf8' },
    { label: 'Mean Diagnosis Time', value: `${data.mean_diagnosis_seconds}s`, color: '#38bdf8' },
    { label: 'Mean Recovery Time (MTTR)', value: `${data.mean_recovery_seconds}s`, color: '#38bdf8' },
    { label: 'Mean Rollback Time', value: `${data.mean_rollback_seconds}s`, color: '#38bdf8' },
    { label: 'Remediation Success Rate', value: `${data.remediation_success_rate_percent}%`, color: '#4ade80' },
    { label: 'False Alert Rate', value: `${data.false_alert_rate_percent}%`, color: '#f87171' },
    { label: 'LLM Total Tokens', value: data.llm_usage_total_tokens.toLocaleString(), color: '#c084fc' },
    { label: 'LLM Estimated Cost', value: `$${data.llm_estimated_cost_usd.toFixed(3)}`, color: '#c084fc' },
  ];

  return (
    <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <h2 style={{ fontSize: '20px', fontWeight: 'bold', color: '#f8fafc' }}>
        📊 Executive Management & Governance Overview
      </h2>

      {/* KPI Cards Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
        {kpis.map((kpi, idx) => (
          <div key={idx} style={{
            backgroundColor: '#1e293b',
            border: '1px solid #334155',
            borderRadius: '8px',
            padding: '20px',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px',
          }}>
            <span style={{ fontSize: '13px', color: '#94a3b8', fontWeight: '500' }}>{kpi.label}</span>
            <span style={{ fontSize: '24px', fontWeight: 'bold', color: kpi.color }}>{kpi.value}</span>
          </div>
        ))}
      </div>

      {/* Release Qualification Banner */}
      <div style={{
        backgroundColor: '#0f172a',
        border: '1px solid #3b82f6',
        borderRadius: '8px',
        padding: '20px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}>
        <div>
          <h3 style={{ fontSize: '16px', fontWeight: 'bold', color: '#38bdf8' }}>🏆 Release Qualification Gate Status</h3>
          <p style={{ fontSize: '14px', color: '#cbd5e1', marginTop: '4px' }}>
            {data.release_qualification_status}
          </p>
        </div>
        <span style={{
          backgroundColor: '#166534',
          color: '#4ade80',
          padding: '8px 16px',
          borderRadius: '6px',
          fontWeight: 'bold',
          fontSize: '14px',
        }}>
          QUALIFIED
        </span>
      </div>
    </div>
  );
};
