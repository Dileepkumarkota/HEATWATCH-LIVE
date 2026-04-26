import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup, Tooltip } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { fetchDistrictRisks, SEVERITY_COLORS } from '../utils/api';

const SEVERITY_ORDER = ['none', 'mild', 'moderate', 'severe', 'extreme'];

export default function MapView() {
  const [districts, setDistricts] = useState([]);
  const [selected, setSelected] = useState(null);
  const [filter, setFilter] = useState('all');

  useEffect(() => { fetchDistrictRisks().then(setDistricts); }, []);

  const filtered = filter === 'all' ? districts : districts.filter(d => d.current_severity === filter);

  function getRadius(d) {
    const idx = SEVERITY_ORDER.indexOf(d.current_severity);
    return 10 + idx * 8;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '22px', fontWeight: '700', color: '#f1f5f9' }}>🗺️ Heatwave Risk Map</h1>
          <p style={{ color: '#64748b', fontSize: '13px' }}>Live district-level severity zones</p>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          {['all', ...SEVERITY_ORDER].map(s => (
            <button
              key={s}
              onClick={() => setFilter(s)}
              style={{
                padding: '6px 14px', borderRadius: '8px', border: 'none', cursor: 'pointer',
                fontSize: '12px', fontWeight: '600',
                background: filter === s ? (SEVERITY_COLORS[s]?.bg || '#3b82f6') : '#1e293b',
                color: filter === s ? '#fff' : '#94a3b8',
              }}
            >
              {s.charAt(0).toUpperCase() + s.slice(1)}
            </button>
          ))}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 300px', gap: '16px' }}>
        {/* Map */}
        <div style={{ borderRadius: '12px', overflow: 'hidden', border: '1px solid #334155', height: '600px' }}>
          <MapContainer center={[20.5937, 78.9629]} zoom={5} style={{ height: '100%', width: '100%' }}>
            <TileLayer
              url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
              attribution='&copy; <a href="https://carto.com">CARTO</a>'
            />
            {filtered.map(d => (
              <CircleMarker
                key={d.district}
                center={[d.lat || d.latitude, d.lng || d.longitude]}
                radius={getRadius(d)}
                pathOptions={{
                  fillColor: SEVERITY_COLORS[d.current_severity]?.bg || '#94a3b8',
                  color: '#fff',
                  weight: 1.5,
                  fillOpacity: 0.75,
                }}
                eventHandlers={{ click: () => setSelected(d) }}
              >
                <Tooltip permanent={false} direction="top">
                  <div style={{ background: '#0f172a', color: '#f1f5f9', padding: '8px 12px', borderRadius: '8px', fontSize: '13px' }}>
                    <strong>{d.district}</strong><br />
                    {d.max_predicted_temp}°C — {d.current_severity?.toUpperCase()}
                  </div>
                </Tooltip>
                <Popup>
                  <div style={{ minWidth: '180px' }}>
                    <strong>{d.district}</strong>, {d.state}<br />
                    Max Temp: {d.max_predicted_temp}°C<br />
                    HW Probability: {Math.round(d.heatwave_probability * 100)}%<br />
                    Severity: <span style={{ color: SEVERITY_COLORS[d.current_severity]?.bg, fontWeight: 'bold' }}>
                      {d.current_severity?.toUpperCase()}
                    </span><br />
                    Vulnerable: {(d.vulnerable_population / 1000).toFixed(0)}K people
                  </div>
                </Popup>
              </CircleMarker>
            ))}
          </MapContainer>
        </div>

        {/* Sidebar */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {/* Legend */}
          <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '16px' }}>
            <h3 style={{ fontSize: '14px', fontWeight: '600', color: '#f1f5f9', marginBottom: '12px' }}>Severity Legend</h3>
            {SEVERITY_ORDER.map(s => (
              <div key={s} style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
                <div style={{ width: '14px', height: '14px', borderRadius: '50%', background: SEVERITY_COLORS[s]?.bg || '#94a3b8' }} />
                <span style={{ fontSize: '13px', color: '#e2e8f0', textTransform: 'capitalize' }}>{s}</span>
              </div>
            ))}
          </div>

          {/* Selected District */}
          {selected && (
            <div style={{ background: '#1e293b', border: `1px solid ${SEVERITY_COLORS[selected.current_severity]?.bg}`, borderRadius: '12px', padding: '16px' }}>
              <h3 style={{ fontSize: '15px', fontWeight: '600', color: '#f1f5f9', marginBottom: '12px' }}>{selected.district}</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {[
                  ['State', selected.state],
                  ['Max Temp', `${selected.max_predicted_temp}°C`],
                  ['HW Probability', `${Math.round(selected.heatwave_probability * 100)}%`],
                  ['Severity', selected.current_severity?.toUpperCase()],
                  ['Vulnerable Pop', `${(selected.vulnerable_population / 1000).toFixed(0)}K`],
                  ['Risk Score', `${selected.risk_score}/100`],
                ].map(([k, v]) => (
                  <div key={k} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
                    <span style={{ color: '#64748b' }}>{k}</span>
                    <span style={{ color: '#f1f5f9', fontWeight: '500' }}>{v}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* District List */}
          <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '16px', flex: 1, overflowY: 'auto' }}>
            <h3 style={{ fontSize: '14px', fontWeight: '600', color: '#f1f5f9', marginBottom: '12px' }}>Districts</h3>
            {districts
              .sort((a, b) => SEVERITY_ORDER.indexOf(b.current_severity) - SEVERITY_ORDER.indexOf(a.current_severity))
              .map(d => (
                <div
                  key={d.district}
                  onClick={() => setSelected(d)}
                  style={{
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    padding: '8px', borderRadius: '6px', cursor: 'pointer', marginBottom: '4px',
                    background: selected?.district === d.district ? '#0f172a' : 'transparent',
                  }}
                >
                  <div>
                    <div style={{ fontSize: '13px', color: '#f1f5f9', fontWeight: '500' }}>{d.district}</div>
                    <div style={{ fontSize: '11px', color: '#64748b' }}>{d.max_predicted_temp}°C</div>
                  </div>
                  <span style={{
                    background: SEVERITY_COLORS[d.current_severity]?.bg,
                    color: '#fff', padding: '2px 8px', borderRadius: '8px',
                    fontSize: '10px', fontWeight: '600',
                  }}>
                    {d.current_severity?.toUpperCase()}
                  </span>
                </div>
              ))}
          </div>
        </div>
      </div>
    </div>
  );
}
