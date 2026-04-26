import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';

const NAV_LINKS = [
  { path: '/',        label: '📊 Dashboard' },
  { path: '/map',     label: '🗺️ Risk Map' },
  { path: '/forecast',label: '📅 Forecast' },
  { path: '/explain', label: '🧠 AI Explain' },
  { path: '/health',  label: '❤️ Health Impact' },
  { path: '/alerts',  label: '🔔 Alerts' },
  { path: '/metrics', label: '📈 Model Metrics' },
];

export default function Navbar() {
  const location = useLocation();
  const [liveTemp, setLiveTemp] = useState(38.4);
  const [activeAlerts, setActiveAlerts] = useState(2);

  useEffect(() => {
    const interval = setInterval(() => {
      setLiveTemp(prev => parseFloat((prev + (Math.random() - 0.5) * 0.2).toFixed(1)));
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <nav style={{
      background: '#1e293b',
      borderBottom: '1px solid #334155',
      padding: '0 24px',
      display: 'flex',
      alignItems: 'center',
      gap: '8px',
      height: '64px',
      position: 'sticky',
      top: 0,
      zIndex: 1000,
    }}>
      {/* Logo */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginRight: '24px' }}>
        <span style={{ fontSize: '24px' }}>🌡️</span>
        <div>
          <div style={{ fontSize: '16px', fontWeight: '700', color: '#f1f5f9', lineHeight: 1 }}>HeatWatch</div>
          <div style={{ fontSize: '10px', color: '#94a3b8', lineHeight: 1 }}>ML Prediction System</div>
        </div>
      </div>

      {/* Nav Links */}
      <div style={{ display: 'flex', gap: '4px', flex: 1, overflowX: 'auto' }}>
        {NAV_LINKS.map(link => (
          <Link
            key={link.path}
            to={link.path}
            style={{
              padding: '8px 12px',
              borderRadius: '8px',
              textDecoration: 'none',
              fontSize: '13px',
              fontWeight: '500',
              whiteSpace: 'nowrap',
              background: location.pathname === link.path ? '#dc2626' : 'transparent',
              color: location.pathname === link.path ? '#fff' : '#94a3b8',
              transition: 'all 0.15s',
            }}
          >
            {link.label}
          </Link>
        ))}
      </div>

      {/* Live Status */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginLeft: '16px' }}>
        <div style={{
          background: '#0f172a',
          border: '1px solid #334155',
          borderRadius: '8px',
          padding: '6px 12px',
          fontSize: '13px',
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
        }}>
          <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#22c55e', display: 'inline-block', animation: 'pulse 2s infinite' }} />
          <span style={{ color: '#94a3b8' }}>Live</span>
          <span style={{ color: '#f97316', fontWeight: '600' }}>{liveTemp}°C</span>
        </div>
        {activeAlerts > 0 && (
          <div style={{
            background: '#dc2626',
            borderRadius: '8px',
            padding: '6px 10px',
            fontSize: '12px',
            fontWeight: '600',
            color: '#fff',
          }}>
            ⚠️ {activeAlerts} Active Alerts
          </div>
        )}
      </div>

      <style>{`
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }
      `}</style>
    </nav>
  );
}
