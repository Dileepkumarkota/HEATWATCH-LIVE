import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { fetchDistrictRisks, fetchWeatherHistory, SEVERITY_COLORS, generateMockForecast } from '../utils/api';

const StatCard = ({ title, value, sub, color = '#3b82f6', icon }) => (
  <div style={{
    background: '#1e293b', border: '1px solid #334155', borderRadius: '12px',
    padding: '20px', borderLeft: `4px solid ${color}`,
  }}>
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
      <div>
        <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{title}</div>
        <div style={{ fontSize: '28px', fontWeight: '700', color: '#f1f5f9' }}>{value}</div>
        {sub && <div style={{ fontSize: '12px', color: '#64748b', marginTop: '4px' }}>{sub}</div>}
      </div>
      <span style={{ fontSize: '28px' }}>{icon}</span>
    </div>
  </div>
);

const SeverityBadge = ({ severity }) => {
  const c = SEVERITY_COLORS[severity] || SEVERITY_COLORS.none;
  return (
    <span style={{
      background: c.bg, color: c.text, padding: '2px 10px',
      borderRadius: '12px', fontSize: '11px', fontWeight: '600', textTransform: 'uppercase',
    }}>{severity}</span>
  );
};

export default function Dashboard() {
  const [districts, setDistricts] = useState([]);
  const [weatherHistory, setWeatherHistory] = useState([]);
  const [selectedDistrict, setSelectedDistrict] = useState('Vijayawada');
  const [forecast, setForecast] = useState(null);
  const [liveData, setLiveData] = useState({ temp: 38.4, humidity: 45, heatIndex: 42.1 });
  const navigate = useNavigate();

  useEffect(() => {
    fetchDistrictRisks().then(setDistricts);
    fetchWeatherHistory(selectedDistrict, 30).then(setWeatherHistory);
    setForecast(generateMockForecast(selectedDistrict));
  }, [selectedDistrict]);

  useEffect(() => {
    const iv = setInterval(() => {
      setLiveData(prev => ({
        temp: parseFloat((prev.temp + (Math.random() - 0.5) * 0.3).toFixed(1)),
        humidity: parseFloat((prev.humidity + (Math.random() - 0.5) * 0.5).toFixed(1)),
        heatIndex: parseFloat((prev.heatIndex + (Math.random() - 0.5) * 0.4).toFixed(1)),
      }));
    }, 2000);
    return () => clearInterval(iv);
  }, []);

  const activeAlerts = districts.filter(d => ['severe', 'extreme'].includes(d.current_severity)).length;
  const heatwaveDistricts = districts.filter(d => d.current_severity !== 'none').length;
  const totalVulnerable = districts.reduce((s, d) => s + (d.vulnerable_population || 0), 0);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '24px', fontWeight: '700', color: '#f1f5f9' }}>Heatwave Prediction Dashboard</h1>
          <p style={{ color: '#64748b', fontSize: '14px', marginTop: '4px' }}>
            ML ensemble — {new Date().toLocaleDateString('en-IN', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
          </p>
        </div>
        <select
          value={selectedDistrict}
          onChange={e => setSelectedDistrict(e.target.value)}
          style={{
            background: '#1e293b', border: '1px solid #334155', color: '#f1f5f9',
            borderRadius: '8px', padding: '8px 12px', fontSize: '14px',
          }}
        >
          {districts.map(d => <option key={d.district} value={d.district}>{d.district}</option>)}
        </select>
      </div>

      {/* Stat Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
        <StatCard title="Live Temperature" value={`${liveData.temp}°C`} sub={selectedDistrict} color="#ef4444" icon="🌡️" />
        <StatCard title="Heat Index" value={`${liveData.heatIndex}°C`} sub="Feels like" color="#f97316" icon="🔥" />
        <StatCard title="Active Alerts" value={activeAlerts} sub="Severe or extreme" color="#dc2626" icon="⚠️" />
        <StatCard title="Affected Districts" value={heatwaveDistricts} sub={`of ${districts.length} monitored`} color="#eab308" icon="📍" />
        <StatCard title="Vulnerable Population" value={`${(totalVulnerable / 1e6).toFixed(1)}M`} sub="At risk across all districts" color="#8b5cf6" icon="👥" />
        <StatCard title="Ensemble Confidence" value={forecast ? `${Math.round(forecast.ensemble_confidence * 100)}%` : '—'} sub="ML prediction confidence" color="#22c55e" icon="🤖" />
      </div>

      {/* Charts Row */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
        {/* Temperature History */}
        <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '20px' }}>
          <h3 style={{ color: '#f1f5f9', marginBottom: '16px', fontSize: '15px', fontWeight: '600' }}>
            📈 30-Day Temperature History — {selectedDistrict}
          </h3>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={weatherHistory.slice(-30)}>
              <defs>
                <linearGradient id="tempGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="date" tick={{ fill: '#64748b', fontSize: 11 }} tickFormatter={d => d.slice(5)} interval={6} />
              <YAxis tick={{ fill: '#64748b', fontSize: 11 }} domain={['auto', 'auto']} />
              <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #334155', color: '#f1f5f9' }} />
              <Area type="monotone" dataKey="temp_max" stroke="#ef4444" fill="url(#tempGrad)" name="Max Temp (°C)" strokeWidth={2} />
              <Area type="monotone" dataKey="heat_index" stroke="#f97316" fill="none" name="Heat Index" strokeWidth={1.5} strokeDasharray="4 2" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* 7-Day Forecast Chart */}
        <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '20px' }}>
          <h3 style={{ color: '#f1f5f9', marginBottom: '16px', fontSize: '15px', fontWeight: '600' }}>
            🔮 7-Day ML Forecast — {selectedDistrict}
          </h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={forecast?.forecast || []}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="date" tick={{ fill: '#64748b', fontSize: 11 }} tickFormatter={d => d.slice(5)} />
              <YAxis tick={{ fill: '#64748b', fontSize: 11 }} domain={[30, 50]} />
              <Tooltip
                contentStyle={{ background: '#0f172a', border: '1px solid #334155', color: '#f1f5f9' }}
                formatter={(v, name) => [`${v}°C`, name]}
              />
              <Bar dataKey="predicted_temp_max" name="Max Temp" fill="#ef4444" radius={[4, 4, 0, 0]} />
              <Bar dataKey="predicted_temp_min" name="Min Temp" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* District Risk Table */}
      <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h3 style={{ color: '#f1f5f9', fontSize: '15px', fontWeight: '600' }}>🗺️ All Districts — Risk Overview</h3>
          <button onClick={() => navigate('/map')} style={{
            background: '#3b82f6', color: '#fff', border: 'none', borderRadius: '8px',
            padding: '6px 14px', fontSize: '13px', cursor: 'pointer',
          }}>View on Map →</button>
        </div>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #334155' }}>
                {['District', 'State', 'Severity', 'Max Temp', 'HW Probability', 'Vulnerable Pop', 'Risk Score'].map(h => (
                  <th key={h} style={{ padding: '10px 12px', textAlign: 'left', color: '#94a3b8', fontWeight: '500', fontSize: '12px' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {districts.map((d, i) => (
                <tr
                  key={d.district}
                  style={{ borderBottom: '1px solid #1e293b', cursor: 'pointer', background: i % 2 === 0 ? 'transparent' : '#0f172a' }}
                  onClick={() => setSelectedDistrict(d.district)}
                >
                  <td style={{ padding: '10px 12px', color: '#f1f5f9', fontWeight: '500' }}>{d.district}</td>
                  <td style={{ padding: '10px 12px', color: '#64748b' }}>{d.state}</td>
                  <td style={{ padding: '10px 12px' }}><SeverityBadge severity={d.current_severity} /></td>
                  <td style={{ padding: '10px 12px', color: '#f97316', fontWeight: '600' }}>{d.max_predicted_temp}°C</td>
                  <td style={{ padding: '10px 12px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <div style={{ flex: 1, height: '6px', background: '#334155', borderRadius: '3px' }}>
                        <div style={{ width: `${d.heatwave_probability * 100}%`, height: '100%', background: '#ef4444', borderRadius: '3px' }} />
                      </div>
                      <span style={{ color: '#f1f5f9', fontSize: '12px', minWidth: '36px' }}>{Math.round(d.heatwave_probability * 100)}%</span>
                    </div>
                  </td>
                  <td style={{ padding: '10px 12px', color: '#8b5cf6' }}>{(d.vulnerable_population / 1000).toFixed(0)}K</td>
                  <td style={{ padding: '10px 12px' }}>
                    <span style={{ color: d.risk_score > 70 ? '#ef4444' : d.risk_score > 40 ? '#f97316' : '#22c55e', fontWeight: '600' }}>
                      {d.risk_score}/100
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Forecast Cards */}
      {forecast && (
        <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '20px' }}>
          <h3 style={{ color: '#f1f5f9', fontSize: '15px', fontWeight: '600', marginBottom: '16px' }}>
            📅 7-Day Detailed Forecast — {selectedDistrict}
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: '8px' }}>
            {forecast.forecast.map(day => {
              const c = SEVERITY_COLORS[day.severity];
              return (
                <div key={day.day} style={{
                  background: '#0f172a', borderRadius: '10px', padding: '12px 8px',
                  textAlign: 'center', border: `1px solid ${day.is_heatwave ? '#ef4444' : '#334155'}`,
                }}>
                  <div style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '6px' }}>
                    {new Date(day.date).toLocaleDateString('en', { weekday: 'short' })}
                  </div>
                  <div style={{ fontSize: '11px', color: '#64748b', marginBottom: '8px' }}>{day.date.slice(5)}</div>
                  <div style={{ fontSize: '20px', fontWeight: '700', color: '#ef4444' }}>{day.predicted_temp_max}°</div>
                  <div style={{ fontSize: '13px', color: '#3b82f6' }}>{day.predicted_temp_min}°</div>
                  <div style={{ marginTop: '8px' }}>
                    <span style={{ background: c.bg, color: c.text, padding: '2px 6px', borderRadius: '8px', fontSize: '10px', fontWeight: '600' }}>
                      {day.severity.toUpperCase()}
                    </span>
                  </div>
                  <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '6px' }}>
                    {Math.round(day.heatwave_probability * 100)}% prob
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
