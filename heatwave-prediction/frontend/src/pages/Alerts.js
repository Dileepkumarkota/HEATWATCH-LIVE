import React, { useState, useEffect } from 'react';
import { SEVERITY_COLORS, getMockDistrictRisks } from '../utils/api';

const MOCK_ALERTS = [
  { id: 1, district: 'Vijayawada', severity: 'severe', type: 'sms', recipient: '+91-944-xxx-0001', status: 'sent', time: '2024-05-14 07:00', message: 'HEATWAVE ALERT: Severe heatwave predicted. Peak 44.2°C on May 16. Activate cooling centres.' },
  { id: 2, district: 'Hyderabad', severity: 'extreme', type: 'email', recipient: 'health@hyderabad.tg.gov.in', status: 'sent', time: '2024-05-14 07:01', message: 'EXTREME HEATWAVE WARNING: 46°C predicted. Declare heat emergency. Vulnerable population: 1.2M at risk.' },
  { id: 3, district: 'Chennai', severity: 'moderate', type: 'push', recipient: 'All registered users', status: 'sent', time: '2024-05-14 07:02', message: 'Heat advisory for Chennai: Moderate heatwave conditions expected. Stay hydrated, avoid outdoor activity 12-3PM.' },
  { id: 4, district: 'Nagpur', severity: 'severe', type: 'sms', recipient: '+91-712-xxx-0004', status: 'failed', time: '2024-05-14 07:03', message: 'HEATWAVE ALERT: Nagpur severe conditions. Emergency services on standby.' },
  { id: 5, district: 'Jaipur', severity: 'mild', type: 'email', recipient: 'health@jaipur.rj.gov.in', status: 'pending', time: '2024-05-14 07:04', message: 'Mild heatwave advisory: Monitor conditions. Open cooling centres as precaution.' },
];

export default function Alerts() {
  const [alerts, setAlerts] = useState(MOCK_ALERTS);
  const [districts, setDistricts] = useState([]);
  const [composing, setComposing] = useState(false);
  const [newAlert, setNewAlert] = useState({ district: 'Vijayawada', type: 'sms', recipient: '' });
  const [sent, setSent] = useState(false);

  useEffect(() => { setDistricts(getMockDistrictRisks()); }, []);

  const stats = {
    total: alerts.length,
    sent: alerts.filter(a => a.status === 'sent').length,
    failed: alerts.filter(a => a.status === 'failed').length,
    pending: alerts.filter(a => a.status === 'pending').length,
  };

  const statusColor = { sent: '#22c55e', failed: '#ef4444', pending: '#eab308' };
  const typeIcon = { sms: '📱', email: '📧', push: '🔔' };

  function handleSend() {
    const alert = {
      id: alerts.length + 1,
      district: newAlert.district,
      severity: districts.find(d => d.district === newAlert.district)?.current_severity || 'moderate',
      type: newAlert.type,
      recipient: newAlert.recipient || '+91-999-000-0000',
      status: 'sent',
      time: new Date().toLocaleString('sv').slice(0, 16),
      message: `Manual heatwave alert triggered for ${newAlert.district}. Check the dashboard for full details.`,
    };
    setAlerts([alert, ...alerts]);
    setSent(true);
    setComposing(false);
    setTimeout(() => setSent(false), 3000);
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '22px', fontWeight: '700', color: '#f1f5f9' }}>🔔 Alert Management</h1>
          <p style={{ color: '#64748b', fontSize: '13px' }}>Automated SMS, Email, and Push notifications to civic authorities</p>
        </div>
        <button onClick={() => setComposing(!composing)} style={{
          background: '#dc2626', color: '#fff', border: 'none', borderRadius: '8px',
          padding: '10px 20px', fontSize: '14px', fontWeight: '600', cursor: 'pointer',
        }}>
          + Send Manual Alert
        </button>
      </div>

      {sent && (
        <div style={{ background: '#052e16', border: '1px solid #22c55e', borderRadius: '10px', padding: '14px 18px', color: '#86efac', fontSize: '14px' }}>
          ✅ Alert sent successfully to civic authorities.
        </div>
      )}

      {/* Compose Panel */}
      {composing && (
        <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '24px' }}>
          <h2 style={{ fontSize: '15px', fontWeight: '600', color: '#f1f5f9', marginBottom: '16px' }}>Compose Alert</h2>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '16px', marginBottom: '16px' }}>
            <div>
              <label style={{ fontSize: '12px', color: '#94a3b8', display: 'block', marginBottom: '6px' }}>District</label>
              <select value={newAlert.district} onChange={e => setNewAlert({ ...newAlert, district: e.target.value })} style={{ width: '100%', background: '#0f172a', border: '1px solid #334155', color: '#f1f5f9', borderRadius: '8px', padding: '8px 12px', fontSize: '14px' }}>
                {districts.map(d => <option key={d.district} value={d.district}>{d.district}</option>)}
              </select>
            </div>
            <div>
              <label style={{ fontSize: '12px', color: '#94a3b8', display: 'block', marginBottom: '6px' }}>Channel</label>
              <select value={newAlert.type} onChange={e => setNewAlert({ ...newAlert, type: e.target.value })} style={{ width: '100%', background: '#0f172a', border: '1px solid #334155', color: '#f1f5f9', borderRadius: '8px', padding: '8px 12px', fontSize: '14px' }}>
                <option value="sms">📱 SMS (Twilio)</option>
                <option value="email">📧 Email (SendGrid)</option>
                <option value="push">🔔 Push (Firebase)</option>
              </select>
            </div>
            <div>
              <label style={{ fontSize: '12px', color: '#94a3b8', display: 'block', marginBottom: '6px' }}>Recipient</label>
              <input value={newAlert.recipient} onChange={e => setNewAlert({ ...newAlert, recipient: e.target.value })} placeholder="+91-xxx or email" style={{ width: '100%', background: '#0f172a', border: '1px solid #334155', color: '#f1f5f9', borderRadius: '8px', padding: '8px 12px', fontSize: '14px' }} />
            </div>
          </div>
          <div style={{ display: 'flex', gap: '10px' }}>
            <button onClick={handleSend} style={{ background: '#dc2626', color: '#fff', border: 'none', borderRadius: '8px', padding: '10px 20px', fontSize: '14px', fontWeight: '600', cursor: 'pointer' }}>
              🚨 Send Alert
            </button>
            <button onClick={() => setComposing(false)} style={{ background: '#334155', color: '#94a3b8', border: 'none', borderRadius: '8px', padding: '10px 20px', fontSize: '14px', cursor: 'pointer' }}>
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
        {[
          { label: 'Total Alerts', value: stats.total, color: '#3b82f6' },
          { label: 'Sent', value: stats.sent, color: '#22c55e' },
          { label: 'Failed', value: stats.failed, color: '#ef4444' },
          { label: 'Pending', value: stats.pending, color: '#eab308' },
        ].map(s => (
          <div key={s.label} style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '16px', borderLeft: `4px solid ${s.color}` }}>
            <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '6px' }}>{s.label}</div>
            <div style={{ fontSize: '28px', fontWeight: '700', color: s.color }}>{s.value}</div>
          </div>
        ))}
      </div>

      {/* Alert Log */}
      <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '20px' }}>
        <h2 style={{ fontSize: '15px', fontWeight: '600', color: '#f1f5f9', marginBottom: '16px' }}>Alert Log</h2>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {alerts.map(alert => (
            <div key={alert.id} style={{
              background: '#0f172a', border: `1px solid ${SEVERITY_COLORS[alert.severity]?.bg || '#334155'}22`,
              borderLeft: `3px solid ${SEVERITY_COLORS[alert.severity]?.bg || '#334155'}`,
              borderRadius: '8px', padding: '14px 16px',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span style={{ fontSize: '18px' }}>{typeIcon[alert.type]}</span>
                  <div>
                    <span style={{ color: '#f1f5f9', fontWeight: '600', fontSize: '14px' }}>{alert.district}</span>
                    <span style={{ color: '#64748b', fontSize: '12px', marginLeft: '8px' }}>{alert.time}</span>
                  </div>
                  <span style={{ background: SEVERITY_COLORS[alert.severity]?.bg, color: '#fff', padding: '2px 8px', borderRadius: '8px', fontSize: '10px', fontWeight: '600' }}>
                    {alert.severity.toUpperCase()}
                  </span>
                </div>
                <span style={{ background: statusColor[alert.status] + '22', color: statusColor[alert.status], padding: '3px 10px', borderRadius: '8px', fontSize: '12px', fontWeight: '600' }}>
                  {alert.status.toUpperCase()}
                </span>
              </div>
              <div style={{ fontSize: '13px', color: '#64748b', marginBottom: '6px' }}>
                → {alert.recipient}
              </div>
              <div style={{ fontSize: '13px', color: '#94a3b8', lineHeight: '1.5' }}>{alert.message}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Alert System Info */}
      <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '20px' }}>
        <h2 style={{ fontSize: '15px', fontWeight: '600', color: '#f1f5f9', marginBottom: '12px' }}>⚙️ Automated Alert Rules</h2>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', fontSize: '14px', color: '#94a3b8' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {[
              ['Trigger threshold', 'Ensemble confidence ≥ 70%'],
              ['Advance warning', '48 hours before predicted onset'],
              ['SMS provider', 'Twilio (auto-retry on failure)'],
              ['Email provider', 'SendGrid with HTML report'],
            ].map(([k, v]) => (
              <div key={k} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px', background: '#0f172a', borderRadius: '6px' }}>
                <span style={{ color: '#64748b' }}>{k}</span>
                <span style={{ color: '#f1f5f9' }}>{v}</span>
              </div>
            ))}
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {[
              ['Push provider', 'Firebase Cloud Messaging'],
              ['Schedule', 'Every 6 hours via Celery Beat'],
              ['Recipients', 'District health officers + DM'],
              ['Escalation', 'Auto-escalate if no ACK in 1hr'],
            ].map(([k, v]) => (
              <div key={k} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px', background: '#0f172a', borderRadius: '6px' }}>
                <span style={{ color: '#64748b' }}>{k}</span>
                <span style={{ color: '#f1f5f9' }}>{v}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
