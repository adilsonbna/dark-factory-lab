import React from 'react';

interface HeaderProps {
  activeTab: 'devops' | 'management';
  setActiveTab: (tab: 'devops' | 'management') => void;
  killSwitchActive: boolean;
  onToggleKillSwitch: (active: boolean) => void;
  overallHealth: string;
}

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  setActiveTab,
  killSwitchActive,
  onToggleKillSwitch,
  overallHealth,
}) => {
  const getHealthBadge = () => {
    if (killSwitchActive) return { bg: '#991b1b', text: 'EMERGENCY HALT' };
    if (overallHealth === 'HEALTHY') return { bg: '#166534', text: 'HEALTHY' };
    if (overallHealth === 'DEGRADED') return { bg: '#854d0e', text: 'DEGRADED' };
    return { bg: '#991b1b', text: 'CRITICAL' };
  };

  const badge = getHealthBadge();

  return (
    <header style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '16px 24px',
      backgroundColor: '#1e293b',
      borderBottom: '1px solid #334155',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <h1 style={{ fontSize: '20px', fontWeight: 'bold', color: '#38bdf8' }}>
          ⚙️ dark-factory-lab
        </h1>
        <span style={{
          backgroundColor: badge.bg,
          color: '#ffffff',
          padding: '4px 10px',
          borderRadius: '12px',
          fontSize: '12px',
          fontWeight: 'bold',
          letterSpacing: '0.5px',
        }}>
          {badge.text}
        </span>
      </div>

      <nav style={{ display: 'flex', gap: '8px' }}>
        <button
          onClick={() => setActiveTab('devops')}
          style={{
            padding: '8px 16px',
            borderRadius: '6px',
            border: 'none',
            backgroundColor: activeTab === 'devops' ? '#0284c7' : '#334155',
            color: '#ffffff',
            fontWeight: 'bold',
            cursor: 'pointer',
          }}
        >
          DevOps View
        </button>
        <button
          onClick={() => setActiveTab('management')}
          style={{
            padding: '8px 16px',
            borderRadius: '6px',
            border: 'none',
            backgroundColor: activeTab === 'management' ? '#0284c7' : '#334155',
            color: '#ffffff',
            fontWeight: 'bold',
            cursor: 'pointer',
          }}
        >
          Management View
        </button>
      </nav>

      <div>
        <button
          onClick={() => onToggleKillSwitch(!killSwitchActive)}
          style={{
            padding: '10px 20px',
            borderRadius: '6px',
            border: '2px solid #ef4444',
            backgroundColor: killSwitchActive ? '#ef4444' : '#7f1d1d',
            color: '#ffffff',
            fontWeight: 'bold',
            fontSize: '14px',
            cursor: 'pointer',
            boxShadow: killSwitchActive ? '0 0 12px #ef4444' : 'none',
            transition: 'all 0.2s ease',
          }}
        >
          🛑 KILL SWITCH: {killSwitchActive ? 'ACTIVE (HALTED)' : 'ARMED'}
        </button>
      </div>
    </header>
  );
};
