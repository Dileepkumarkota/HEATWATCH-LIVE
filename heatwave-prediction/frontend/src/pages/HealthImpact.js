import React, { useState, useEffect } from 'react';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts';
import { generateMockForecast, DISTRICTS, SEVERITY_COLORS } from '../utils/api';

export default function HealthImpact() {
  const [district, setDistrict] = useState('Vijayawada');
  const [data, setData] = useState(null);

  useEffect(() => {
    const forecast = generateMockForecast(district);
    setData(forecast);
  }, [district]);

  if (!data) return <div style={{ color: '#94a3b8' }}>Loading...</div>;

  const health = data.health_risk;
  const pieData = [
    { name: 'Elderly (65+)', value: health.elderly_at_risk, color: '#ef4444' },
    { name: 'Children (<5)', value: health.children_at_risk, color: '#f97316' },
    { name: 'Other vulnerable', value: health.vulnerable_population - health.elderly_at_risk - health.children_at_risk, color: '#eab308' },
    { name: 'Not at risk', value: health.total_population - health.vulnerable_population, color: '#334155' },
  ];

  const riskLevelColor = { low: '#22c55e', moderate: '#eab308', high: '#f97316', very_high: '#ef4444' };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '22px', fontWeight: '700', color: '#f1f5f9' }}>❤️ Health Impact Assessment</h1>
          <p style={{ color: '#64748b', fontSize: '13px' }}>Vulnerable population mapping and health risk quantification</p>
        </div>
        <select value={district} onChange={e => setDistrict(e.target.value)} style={{
          background: '#1e293b', border: '1px solid #334155', color: '#f1f5f9',
          borderRadius: '8px', padding: '8px 12px', fontSize: '14px',
        }}>
          {DISTRICTS.map(d => <option key={d.name} value={d.name}>{d.name}</option>)}
        </select>
      </div>

      {/* Risk Level Banner */}
      <div style={{
        background: '#1e293b', border: `2px solid ${riskLevelColor[health.risk_level] || '#64748b'}`,
        borderRadius: '12px', padding: '20px', display: 'flex', alignItems: 'center', gap: '20px',
      }}>
        <div style={{ fontSize: '48px' }}>
          {{ low: '🟢', moderate: '🟡', high: '🟠', very_high: '🔴' }[health.risk_level] || '⚪'}
        </div>
        <div>
          <div style={{ fontSize: '12px', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.1em' }}>Overall Health Risk Level</div>
          <div style={{ fontSize: '28px', fontWeight: '700', color: riskLevelColor[health.risk_level], textTransform: 'uppercase' }}>
            {health.risk_level?.replace('_', ' ')}
          </div>
          <div style={{ fontSize: '13px', color: '#64748b', marginTop: '4px' }}>
            Peak severity: <strong style={{ color: '#f97316' }}>{health.peak_severity?.toUpperCase()}</strong> on {health.peak_date}
          </div>
        </div>
        <div style={{ marginLeft: 'auto', textAlign: 'right' }}>
          <div style={{ fontSize: '12px', color: '#94a3b8' }}>Ensemble confidence</div>
          <div style={{ fontSize: '24px', fontWeight: '700', color: '#f1f5f9' }}>
            {Math.round(data.ensemble_confidence * 100)}%
          </div>
        </div>
      </div>

      {/* Population Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
        {[
          { label: 'Total Population', value: health.total_population?.toLocaleString(), icon: '👥', color: '#3b82f6' },
          { label: 'Vulnerable Population', value: health.vulnerable_population?.toLocaleString(), icon: '⚠️', color: '#f97316' },
          { label: 'Elderly at Risk (65+)', value: health.elderly_at_risk?.toLocaleString(), icon: '👴', color: '#ef4444' },
          { label: 'Children at Risk (<5)', value: health.children_at_risk?.toLocaleString(), icon: '👶', color: '#eab308' },
        ].map(c => (
          <div key={c.label} style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '16px', borderLeft: `4px solid ${c.color}` }}>
            <div style={{ fontSize: '24px', marginBottom: '8px' }}>{c.icon}</div>
            <div style={{ fontSize: '22px', fontWeight: '700', color: '#f1f5f9' }}>{c.value}</div>
            <div style={{ fontSize: '12px', color: '#64748b', marginTop: '4px' }}>{c.label}</div>
          </div>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
        {/* Pie Chart */}
        <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '24px' }}>
          <h2 style={{ fontSize: '15px', fontWeight: '600', color: '#f1f5f9', marginBottom: '16px' }}>Population Risk Breakdown</h2>
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie data={pieData} cx="50%" cy="50%" outerRadius={100} dataKey="value" label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`} labelLine={false}>
                {pieData.map((entry, i) => <Cell key={i} fill={entry.color} />)}
              </Pie>
              <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #334155', color: '#f1f5f9' }}
                formatter={v => v.toLocaleString()} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Recommended Actions */}
        <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '24px' }}>
          <h2 style={{ fontSize: '15px', fontWeight: '600', color: '#f1f5f9', marginBottom: '16px' }}>🚨 Recommended Actions</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {(data.recommended_actions || []).map((action, i) => (
              <div key={i} style={{
                display: 'flex', alignItems: 'flex-start', gap: '10px',
                background: '#0f172a', borderRadius: '8px', padding: '12px',
              }}>
                <span style={{ color: '#ef4444', fontWeight: '700', minWidth: '20px' }}>{i + 1}.</span>
                <span style={{ fontSize: '14px', color: '#e2e8f0', lineHeight: '1.5' }}>{action}</span>
              </div>
            ))}
          </div>

          {/* Cooling Centres */}
          {data.cooling_centres?.length > 0 && (
            <div style={{ marginTop: '20px' }}>
              <h3 style={{ fontSize: '14px', fontWeight: '600', color: '#f1f5f9', marginBottom: '10px' }}>❄️ Nearest Cooling Centres</h3>
              {data.cooling_centres.map((c, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px', fontSize: '13px' }}>
                  <span>📍</span>
                  <span style={{ color: '#94a3b8' }}>{c.name}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
