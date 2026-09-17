import React, { useEffect, useState } from 'react';
import { Header } from './components/Header';
import { DevOpsView } from './components/DevOpsView';
import { ManagementView } from './components/ManagementView';
import { DevOpsViewData, ManagementViewData } from './types';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'devops' | 'management'>('devops');
  const [devopsData, setDevopsData] = useState<DevOpsViewData | null>(null);
  const [managementData, setManagementData] = useState<ManagementViewData | null>(null);

  const fetchDevOps = async () => {
    try {
      const res = await fetch('/api/v1/dashboard/devops');
      if (res.ok) {
        const data: DevOpsViewData = await res.json();
        setDevopsData(data);
      }
    } catch (e) {
      console.error('Failed to fetch DevOps view data:', e);
    }
  };

  const fetchManagement = async () => {
    try {
      const res = await fetch('/api/v1/dashboard/management');
      if (res.ok) {
        const data: ManagementViewData = await res.json();
        setManagementData(data);
      }
    } catch (e) {
      console.error('Failed to fetch Management view data:', e);
    }
  };

  const handleToggleKillSwitch = async (active: boolean) => {
    let operatorToken = window.sessionStorage.getItem('operator_token');
    if (!operatorToken) {
      operatorToken = window.prompt('Enter the local operator token to change automation state:');
      if (!operatorToken) return;
      window.sessionStorage.setItem('operator_token', operatorToken);
    }
    try {
      const res = await fetch('/api/v1/dashboard/kill-switch', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${operatorToken}`,
        },
        body: JSON.stringify({ active, reason: 'Operator UI toggle' }),
      });
      if (res.ok) {
        fetchDevOps();
        fetchManagement();
      } else if (res.status === 401 || res.status === 503) {
        window.sessionStorage.removeItem('operator_token');
        window.alert('Operator authentication failed. The token was not retained.');
      }
    } catch (e) {
      console.error('Failed to toggle kill switch:', e);
    }
  };

  useEffect(() => {
    fetchDevOps();
    fetchManagement();
    const interval = setInterval(() => {
      fetchDevOps();
      fetchManagement();
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div>
      <Header
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        killSwitchActive={devopsData?.kill_switch_active || false}
        onToggleKillSwitch={handleToggleKillSwitch}
        overallHealth={managementData?.overall_health || 'HEALTHY'}
      />

      <main>
        {activeTab === 'devops' ? (
          <DevOpsView
            activeIncidents={devopsData?.active_incidents || []}
            resolvedIncidents={devopsData?.resolved_incidents || []}
            killSwitchActive={devopsData?.kill_switch_active || false}
          />
        ) : (
          <ManagementView data={managementData} />
        )}
      </main>
    </div>
  );
};

export default App;
