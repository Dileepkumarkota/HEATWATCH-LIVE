import React, { useState, useEffect } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import { generateMockForecast, DISTRICTS, SEVERITY_COLORS } from '../utils/api';

export default function Forecast() {
  const [district, setDistrict] = useState('Vijayawada');
  const [data, setData] = useState(null);

  useEffect(() => { setData(generateMockForecast(district)); }, [district]);

  if (!data) return <div style={{ color: '#94a3b8' }}>Loading...</div>;

  const chartData = data.forecast.map(d => ({
    date: d.date.slice(5),
    max: d.predicted_temp_max,
    min: d.predicted_temp_min,
    upper: d.confidence_upper,
    lower: d.confidence_lower,
    prob: Math.round(d.heatwave_probability * 100),
  }));

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '22px', fontWeight: '700', color: '#f1f5f9' }}>📅 7-Day Heatwave Forecast</h1>
          <p style={{ color: '#64748b', fontSize: '13px' }}>LSTM neural network prediction with 95% confidence intervals</p>
        </div>
        <select value={district} onChange={e => setDistrict(e.target.value)} style={{
          background: '#1e293b', border: '1px solid #334155', color: '#f1f5f9',
          borderRadius: '8px', padding: '8px 12px', fontSize: '14px',
        }}>
          {DISTRICTS.map(d => <option key={d.name} value={d.name}>{d.name}</option>)}
        </select>
      </div>

      {/* Confidence band chart */}
      <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '24px' }}>
        <h2 style={{ fontSize: '15px', fontWeight: '600', color: '#f1f5f9', marginBottom: '16px' }}>
          Temperature Forecast with 95% Confidence Interval
        </h2>
        <ResponsiveContainer width="100%" height={260}>
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id="ciGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#ef4444" stopOpacity={0.15} />
                <stop offset="95%" stopColor="#ef4444" stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="date" tick={{ fill: '#64748b', fontSize: 12 }} />
            <YAxis tick={{ fill: '#64748b', fontSize: 12 }} domain={['auto', 'auto']} unit="°C" />
            <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #334155', color: '#f1f5f9' }}
              formatter={(v, n) => [`${v}°C`, n]} />
            <ReferenceLine y={40} stroke="#ef4444" strokeDasharray="6 3" label={{ value: 'HW Threshold 40°C', fill: '#ef4444', fontSize: 11 }} />
            <Area type="monotone" dataKey="upper" stroke="none" fill="url(#ciGrad)" name="Upper CI" />
            <Area type="monotone" dataKey="lower" stroke="none" fill="#0f172a" name="Lower CI" />
            <Area type="monotone" dataKey="max" stroke="#ef4444" fill="none" strokeWidth={2.5} name="Max Temp" dot={{ fill: '#ef4444', r: 4 }} />
            <Area type="monotone" dataKey="min" stroke="#3b82f6" fill="none" strokeWidth={2} name="Min Temp" dot={{ fill: '#3b82f6', r: 3 }} />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* HW Probability chart */}
      <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '24px' }}>
        <h2 style={{ fontSize: '15px', fontWeight: '600', color: '#f1f5f9', marginBottom: '16px' }}>
          Heatwave Probability — XGBoost Classifier
        </h2>
        <ResponsiveContainer width="100%" height={160}>
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id="probGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#f97316" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#f97316" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="date" tick={{ fill: '#64748b', fontSize: 12 }} />
            <YAxis tick={{ fill: '#64748b', fontSize: 12 }} unit="%" domain={[0, 100]} />
            <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #334155', color: '#f1f5f9' }}
              formatter={v => [`${v}%`, 'HW Probability']} />
            <ReferenceLine y={70} stroke="#ef4444" strokeDasharray="4 2" label={{ value: 'Alert threshold 70%', fill: '#ef4444', fontSize: 11 }} />
            <Area type="monotone" dataKey="prob" stroke="#f97316" fill="url(#probGrad)" strokeWidth={2} name="HW Probability" />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Day cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: '10px' }}>
        {data.forecast.map(day => {
          const c = SEVERITY_COLORS[day.severity];
          const dayName = new Date(day.date).toLocaleDateString('en', { weekday: 'short' });
          return (
            <div key={day.day} style={{
              background: '#1e293b',
              border: `1px solid ${day.is_heatwave ? c.bg : '#334155'}`,
              borderRadius: '12px', padding: '16px', textAlign: 'center',
              boxShadow: day.is_heatwave ? `0 0 12px ${c.bg}33` : 'none',
            }}>
              <div style={{ fontSize: '11px', color: '#94a3b8', fontWeight: '600', textTransform: 'uppercase' }}>{dayName}</div>
              <div style={{ fontSize: '11px', color: '#475569', marginBottom: '10px' }}>{day.date.slice(5)}</div>
              {day.is_heatwave && <div style={{ fontSize: '20px', marginBottom: '6px' }}>🔥</div>}
              <div style={{ fontSize: '22px', fontWeight: '700', color: '#ef4444' }}>{day.predicted_temp_max}°</div>
              <div style={{ fontSize: '14px', color: '#3b82f6', marginBottom: '8px' }}>{day.predicted_temp_min}°</div>
              <div style={{ fontSize: '10px', color: '#475569', marginBottom: '8px' }}>
                {day.confidence_lower}° – {day.confidence_upper}°
              </div>
              <span style={{ background: c.bg, color: '#fff', padding: '3px 8px', borderRadius: '8px', fontSize: '10px', fontWeight: '700' }}>
                {day.severity.toUpperCase()}
              </span>
              <div style={{ fontSize: '12px', color: '#64748b', marginTop: '8px' }}>
                {Math.round(day.heatwave_probability * 100)}% HW prob
              </div>
              <div style={{ height: '4px', background: '#334155', borderRadius: '2px', marginTop: '8px' }}>
                <div style={{ width: `${day.heatwave_probability * 100}%`, height: '100%', background: c.bg, borderRadius: '2px' }} />
              </div>
            </div>
          );
        })}
      </div>

      {/* Model info */}
      <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '20px' }}>
        <h2 style={{ fontSize: '15px', fontWeight: '600', color: '#f1f5f9', marginBottom: '12px' }}>🤖 How This Forecast Was Made</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', fontSize: '13px' }}>
          {[
            { model: 'LSTM Network', role: 'Temperature sequences', detail: '2-layer bidirectional LSTM with attention mechanism. Input: 30-day sliding window. Output: 7-day temp forecast with MC dropout uncertainty.', color: '#3b82f6' },
            { model: 'XGBoost Classifier', role: 'Onset probability', detail: '500 estimators, 50+ engineered features. Uses IMD definition: Tmax ≥ 40°C AND departure ≥ 4.5°C. AUC-ROC: 0.943.', color: '#f97316' },
            { model: 'Random Forest', role: 'Severity scoring', detail: '300 estimators with demographic weighting. Incorporates population density, green cover, UHI score into severity classification.', color: '#22c55e' },
          ].map(m => (
            <div key={m.model} style={{ borderLeft: `3px solid ${m.color}`, paddingLeft: '12px' }}>
              <div style={{ fontWeight: '600', color: '#f1f5f9', marginBottom: '4px' }}>{m.model}</div>
              <div style={{ color: m.color, fontSize: '11px', marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{m.role}</div>
              <div style={{ color: '#64748b', lineHeight: '1.6' }}>{m.detail}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
