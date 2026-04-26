import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import { fetchExplanation, DISTRICTS } from '../utils/api';

export default function Explainability() {
  const [district, setDistrict] = useState('Vijayawada');
  const [explanation, setExplanation] = useState(null);

  useEffect(() => { fetchExplanation(district).then(setExplanation); }, [district]);

  const chartData = explanation?.explanation?.map(e => ({
    feature: e.feature.replace(/_/g, ' '),
    value: parseFloat(e.shap_value.toFixed(4)),
    color: e.shap_value > 0 ? '#ef4444' : '#22c55e',
  })) || [];

  const baseVal = explanation?.base_value || 0.35;
  const predVal = explanation?.prediction_value || 0.72;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '22px', fontWeight: '700', color: '#f1f5f9' }}>🧠 AI Explainability (SHAP)</h1>
          <p style={{ color: '#64748b', fontSize: '13px', marginTop: '4px' }}>
            Why did the model predict a heatwave? SHAP values show each feature's contribution.
          </p>
        </div>
        <select value={district} onChange={e => setDistrict(e.target.value)} style={{
          background: '#1e293b', border: '1px solid #334155', color: '#f1f5f9',
          borderRadius: '8px', padding: '8px 12px', fontSize: '14px',
        }}>
          {DISTRICTS.map(d => <option key={d.name} value={d.name}>{d.name}</option>)}
        </select>
      </div>

      {/* Prediction Summary */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
        {[
          { label: 'Base Value (avg prediction)', value: `${(baseVal * 100).toFixed(0)}%`, color: '#64748b', desc: 'Average HW probability across all training data' },
          { label: 'SHAP Adjustment', value: `+${((predVal - baseVal) * 100).toFixed(0)}%`, color: '#ef4444', desc: 'Sum of all feature SHAP contributions' },
          { label: 'Final Prediction', value: `${(predVal * 100).toFixed(0)}%`, color: '#f97316', desc: 'Heatwave probability for this district' },
        ].map(card => (
          <div key={card.label} style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '20px' }}>
            <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '8px' }}>{card.label}</div>
            <div style={{ fontSize: '28px', fontWeight: '700', color: card.color }}>{card.value}</div>
            <div style={{ fontSize: '12px', color: '#475569', marginTop: '4px' }}>{card.desc}</div>
          </div>
        ))}
      </div>

      {/* SHAP Waterfall Chart */}
      <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '24px' }}>
        <h2 style={{ fontSize: '16px', fontWeight: '600', color: '#f1f5f9', marginBottom: '8px' }}>
          SHAP Feature Importance — {district}
        </h2>
        <p style={{ fontSize: '13px', color: '#64748b', marginBottom: '20px' }}>
          Red bars push the prediction <strong style={{ color: '#ef4444' }}>towards heatwave</strong>.
          Green bars push it <strong style={{ color: '#22c55e' }}>away from heatwave</strong>.
        </p>
        <ResponsiveContainer width="100%" height={320}>
          <BarChart data={chartData} layout="vertical" margin={{ left: 160 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" horizontal={false} />
            <XAxis type="number" tick={{ fill: '#64748b', fontSize: 11 }} domain={[-0.3, 0.6]} tickFormatter={v => v.toFixed(2)} />
            <YAxis type="category" dataKey="feature" tick={{ fill: '#e2e8f0', fontSize: 12 }} width={155} />
            <Tooltip
              contentStyle={{ background: '#0f172a', border: '1px solid #334155', color: '#f1f5f9' }}
              formatter={(v) => [v > 0 ? `+${v.toFixed(4)} (increases risk)` : `${v.toFixed(4)} (decreases risk)`, 'SHAP Value']}
            />
            <ReferenceLine x={0} stroke="#475569" strokeWidth={2} />
            <Bar dataKey="value" radius={[0, 4, 4, 0]}
              fill="#ef4444"
              label={{ position: 'insideRight', fill: '#f1f5f9', fontSize: 11, formatter: v => v > 0 ? `+${v.toFixed(3)}` : v.toFixed(3) }}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Feature Details Table */}
      <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '24px' }}>
        <h2 style={{ fontSize: '16px', fontWeight: '600', color: '#f1f5f9', marginBottom: '16px' }}>Feature Contribution Details</h2>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid #334155' }}>
              {['Rank', 'Feature', 'SHAP Value', 'Direction', 'Interpretation'].map(h => (
                <th key={h} style={{ padding: '10px 12px', textAlign: 'left', color: '#94a3b8', fontWeight: '500', fontSize: '12px' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {explanation?.explanation?.map((e, i) => (
              <tr key={e.feature} style={{ borderBottom: '1px solid #0f172a' }}>
                <td style={{ padding: '10px 12px', color: '#64748b' }}>#{e.importance_rank || i + 1}</td>
                <td style={{ padding: '10px 12px', color: '#f1f5f9', fontFamily: 'monospace', fontSize: '13px' }}>{e.feature}</td>
                <td style={{ padding: '10px 12px', color: e.shap_value > 0 ? '#ef4444' : '#22c55e', fontWeight: '600' }}>
                  {e.shap_value > 0 ? '+' : ''}{e.shap_value.toFixed(4)}
                </td>
                <td style={{ padding: '10px 12px' }}>
                  <span style={{
                    background: e.direction === 'increases_risk' ? '#450a0a' : '#052e16',
                    color: e.direction === 'increases_risk' ? '#fca5a5' : '#86efac',
                    padding: '2px 8px', borderRadius: '8px', fontSize: '11px',
                  }}>
                    {e.direction === 'increases_risk' ? '↑ Increases risk' : '↓ Decreases risk'}
                  </span>
                </td>
                <td style={{ padding: '10px 12px', color: '#94a3b8', fontSize: '12px' }}>
                  {FEATURE_INTERPRETATIONS[e.feature] || 'Weather or climate feature'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Explanation Box */}
      <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '24px' }}>
        <h2 style={{ fontSize: '16px', fontWeight: '600', color: '#f1f5f9', marginBottom: '12px' }}>📖 Why SHAP Explainability Matters</h2>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', fontSize: '14px', color: '#94a3b8', lineHeight: '1.7' }}>
          <div>
            <p><strong style={{ color: '#f1f5f9' }}>What is SHAP?</strong></p>
            <p>SHAP (SHapley Additive exPlanations) is a game-theory-based method that explains the output of any ML model. It assigns each feature an importance value for a specific prediction, showing exactly how each variable pushes the model's output up or down.</p>
          </div>
          <div>
            <p><strong style={{ color: '#f1f5f9' }}>Why it matters for heatwave alerts</strong></p>
            <p>Without explainability, authorities must blindly trust the model. With SHAP, they can verify: "High risk because temperature anomaly is +6°C and 8 consecutive hot days have been recorded." This makes the system auditable and trustworthy for civic decision-making.</p>
          </div>
        </div>
      </div>
    </div>
  );
}

const FEATURE_INTERPRETATIONS = {
  temp_max_anomaly: 'How much hotter than the 30-year normal for this date',
  consecutive_hot_days: 'Number of consecutive days with Tmax ≥ 38°C',
  heat_index: 'Apparent temperature accounting for humidity (feels-like)',
  uhi_score: 'Urban Heat Island intensity — urban areas trap more heat',
  humidity_anomaly: 'Deviation from normal humidity levels',
  green_cover_pct: 'Higher green cover reduces urban heat absorption',
  wind_speed: 'Higher wind disperses heat and lowers risk',
  pressure_change: '24-hour pressure drop can signal incoming heat dome',
  temp_max_lag7: 'Max temperature 7 days ago — persistence signal',
  month_sin: 'Cyclical time feature encoding seasonal position',
};
