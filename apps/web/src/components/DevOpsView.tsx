import React, { useState } from 'react';
import { IncidentItem } from '../types';

interface DevOpsViewProps {
  activeIncidents: IncidentItem[];
  resolvedIncidents: IncidentItem[];
  killSwitchActive: boolean;
}

export const DevOpsView: React.FC<DevOpsViewProps> = ({
  activeIncidents,
  resolvedIncidents,
  killSwitchActive,
}) => {
  const [selectedIncident, setSelectedIncident] = useState<IncidentItem | null>(
    activeIncidents.length > 0 ? activeIncidents[0] : resolvedIncidents.length > 0 ? resolvedIncidents[0] : null
  );

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Detected': return '#f59e0b';
      case 'Triaged': return '#3b82f6';
      case 'Investigating': return '#8b5cf6';
      case 'Fix proposed': return '#ec4899';
      case 'Validating': return '#6366f1';
      case 'Approved': return '#10b981';
      case 'Deploying': return '#06b6d4';
      case 'Observing': return '#14b8a6';
      case 'Resolved': return '#22c55e';
      case 'Rolled back': return '#ef4444';
      case 'Escalated': return '#dc2626';
      default: return '#64748b';
    }
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '20px', padding: '24px' }}>
      {/* Sidebar: Incident List */}
      <div style={{ backgroundColor: '#1e293b', borderRadius: '8px', padding: '16px', border: '1px solid #334155' }}>
        <h2 style={{ fontSize: '16px', fontWeight: 'bold', color: '#94a3b8', marginBottom: '16px' }}>
          Active Incidents ({activeIncidents.length})
        </h2>

        {activeIncidents.length === 0 ? (
          <p style={{ color: '#64748b', fontSize: '14px', fontStyle: 'italic', marginBottom: '20px' }}>
            No active incidents. System healthy.
          </p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '24px' }}>
            {activeIncidents.map((inc) => (
              <div
                key={inc.id}
                onClick={() => setSelectedIncident(inc)}
                style={{
                  padding: '12px',
                  borderRadius: '6px',
                  backgroundColor: selectedIncident?.id === inc.id ? '#334155' : '#0f172a',
                  borderLeft: `4px solid ${getStatusColor(inc.status)}`,
                  cursor: 'pointer',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <span style={{ fontSize: '12px', fontWeight: 'bold', color: '#38bdf8' }}>{inc.id}</span>
                  <span style={{
                    fontSize: '11px',
                    padding: '2px 6px',
                    borderRadius: '4px',
                    backgroundColor: getStatusColor(inc.status),
                    color: '#fff',
                  }}>
                    {inc.status}
                  </span>
                </div>
                <h4 style={{ fontSize: '14px', color: '#f8fafc', marginBottom: '4px' }}>{inc.title}</h4>
                <span style={{ fontSize: '12px', color: '#94a3b8' }}>Service: {inc.affected_service}</span>
              </div>
            ))}
          </div>
        )}

        <h2 style={{ fontSize: '16px', fontWeight: 'bold', color: '#94a3b8', marginBottom: '16px' }}>
          Resolved History ({resolvedIncidents.length})
        </h2>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {resolvedIncidents.map((inc) => (
            <div
              key={inc.id}
              onClick={() => setSelectedIncident(inc)}
              style={{
                padding: '12px',
                borderRadius: '6px',
                backgroundColor: selectedIncident?.id === inc.id ? '#334155' : '#0f172a',
                borderLeft: `4px solid ${getStatusColor(inc.status)}`,
                cursor: 'pointer',
                opacity: 0.8,
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                <span style={{ fontSize: '12px', fontWeight: 'bold', color: '#38bdf8' }}>{inc.id}</span>
                <span style={{
                  fontSize: '11px',
                  padding: '2px 6px',
                  borderRadius: '4px',
                  backgroundColor: getStatusColor(inc.status),
                  color: '#fff',
                }}>
                  {inc.status}
                </span>
              </div>
              <h4 style={{ fontSize: '13px', color: '#cbd5e1' }}>{inc.title}</h4>
            </div>
          ))}
        </div>
      </div>

      {/* Main Inspector Panel */}
      <div style={{ backgroundColor: '#1e293b', borderRadius: '8px', padding: '24px', border: '1px solid #334155' }}>
        {selectedIncident ? (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', borderBottom: '1px solid #334155', paddingBottom: '16px' }}>
              <div>
                <span style={{ fontSize: '14px', fontWeight: 'bold', color: '#38bdf8' }}>{selectedIncident.id}</span>
                <h1 style={{ fontSize: '22px', fontWeight: 'bold', color: '#f8fafc', marginTop: '4px' }}>{selectedIncident.title}</h1>
              </div>
              <span style={{
                padding: '6px 14px',
                borderRadius: '6px',
                backgroundColor: getStatusColor(selectedIncident.status),
                color: '#ffffff',
                fontWeight: 'bold',
                fontSize: '14px',
              }}>
                {selectedIncident.status}
              </span>
            </div>

            {/* Hypothesis & Ground Truth */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '20px' }}>
              <div style={{ backgroundColor: '#0f172a', padding: '16px', borderRadius: '6px' }}>
                <h3 style={{ fontSize: '14px', color: '#94a3b8', marginBottom: '8px' }}>🔍 Root Cause Hypothesis</h3>
                <p style={{ fontSize: '14px', color: '#e2e8f0' }}>{selectedIncident.hypothesis || 'Pending Investigation'}</p>
              </div>
              <div style={{ backgroundColor: '#0f172a', padding: '16px', borderRadius: '6px' }}>
                <h3 style={{ fontSize: '14px', color: '#94a3b8', marginBottom: '8px' }}>🎯 Verified Root Cause</h3>
                <p style={{ fontSize: '14px', color: '#e2e8f0' }}>{selectedIncident.root_cause || 'Analyzing...'}</p>
              </div>
            </div>

            {/* Remediation Diff */}
            {selectedIncident.remediation_diff && (
              <div style={{ marginBottom: '20px' }}>
                <h3 style={{ fontSize: '14px', color: '#94a3b8', marginBottom: '8px' }}>🛠️ Proposed PR Code Diff</h3>
                <pre style={{
                  backgroundColor: '#090d16',
                  padding: '16px',
                  borderRadius: '6px',
                  color: '#4ade80',
                  fontFamily: 'monospace',
                  fontSize: '13px',
                  overflowX: 'auto',
                }}>
                  {selectedIncident.remediation_diff}
                </pre>
              </div>
            )}

            {/* Agent Timeline */}
            <div style={{ marginBottom: '20px' }}>
              <h3 style={{ fontSize: '14px', color: '#94a3b8', marginBottom: '12px' }}>🤖 Agent Execution Timeline</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {selectedIncident.agent_timeline.map((step, idx) => (
                  <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '12px', backgroundColor: '#0f172a', padding: '10px 14px', borderRadius: '6px' }}>
                    <span style={{ fontSize: '12px', color: '#64748b', fontFamily: 'monospace' }}>{step.timestamp}</span>
                    <span style={{ fontSize: '12px', fontWeight: 'bold', color: '#38bdf8' }}>[{step.agent}]</span>
                    <span style={{ fontSize: '13px', color: '#e2e8f0' }}>{step.action}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Audit Trail */}
            <div>
              <h3 style={{ fontSize: '14px', color: '#94a3b8', marginBottom: '12px' }}>📜 Immutable Audit Records</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {selectedIncident.audit_trail.map((record, idx) => (
                  <div key={idx} style={{ fontSize: '12px', color: '#cbd5e1', backgroundColor: '#0f172a', padding: '8px 12px', borderRadius: '4px', fontFamily: 'monospace' }}>
                    [{record.timestamp}] EVENT: <strong>{record.event}</strong> | ACTOR: {record.actor} {record.reason ? `| REASON: ${record.reason}` : ''}
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <p style={{ color: '#64748b' }}>Select an incident to view details.</p>
        )}
      </div>
    </div>
  );
};
