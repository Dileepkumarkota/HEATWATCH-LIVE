import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import MapView from './pages/MapView';
import Forecast from './pages/Forecast';
import Explainability from './pages/Explainability';
import HealthImpact from './pages/HealthImpact';
import Alerts from './pages/Alerts';
import ModelMetrics from './pages/ModelMetrics';

export default function App() {
  return (
    <Router>
      <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
        <Navbar />
        <main style={{ flex: 1, padding: '24px', maxWidth: '1400px', margin: '0 auto', width: '100%' }}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/map" element={<MapView />} />
            <Route path="/forecast" element={<Forecast />} />
            <Route path="/explain" element={<Explainability />} />
            <Route path="/health" element={<HealthImpact />} />
            <Route path="/alerts" element={<Alerts />} />
            <Route path="/metrics" element={<ModelMetrics />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}
