import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: `${API_BASE}/api/v1`,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

// ── Mock data for demo (used when backend is not running) ──────────────────
const DISTRICTS = [
  { name: 'Vijayawada', state: 'Andhra Pradesh', lat: 16.5062, lng: 80.6480 },
  { name: 'Hyderabad',  state: 'Telangana',       lat: 17.3850, lng: 78.4867 },
  { name: 'Chennai',    state: 'Tamil Nadu',       lat: 13.0827, lng: 80.2707 },
  { name: 'Nagpur',     state: 'Maharashtra',      lat: 21.1458, lng: 79.0882 },
  { name: 'Jaipur',     state: 'Rajasthan',        lat: 26.9124, lng: 75.7873 },
  { name: 'Ahmedabad',  state: 'Gujarat',          lat: 23.0225, lng: 72.5714 },
  { name: 'Bhubaneswar',state: 'Odisha',           lat: 20.2961, lng: 85.8245 },
  { name: 'Lucknow',    state: 'Uttar Pradesh',    lat: 26.8467, lng: 80.9462 },
];

const SEVERITIES = ['none', 'mild', 'moderate', 'severe', 'extreme'];
const SEVERITY_PROBS = [0.25, 0.30, 0.25, 0.15, 0.05];

function weightedRandom(items, weights, seed) {
  let x = Math.sin(seed) * 10000;
  const r = x - Math.floor(x);
  let cumulative = 0;
  for (let i = 0; i < items.length; i++) {
    cumulative += weights[i];
    if (r < cumulative) return items[i];
  }
  return items[items.length - 1];
}

function seededRandom(seed) {
  let x = Math.sin(seed + 1) * 10000;
  return x - Math.floor(x);
}

export function generateMockForecast(district = 'Vijayawada') {
  const seed = district.charCodeAt(0) + district.charCodeAt(1);
  const baseTemp = 36 + seededRandom(seed) * 8;
  const forecast = [];
  const today = new Date();

  for (let i = 0; i < 7; i++) {
    const date = new Date(today);
    date.setDate(today.getDate() + i + 1);
    const temp = baseTemp + i * 0.6 + (seededRandom(seed + i) - 0.5) * 2;
    const prob = Math.min(0.95, 0.3 + seededRandom(seed + i * 3) * 0.6);
    const sev = weightedRandom(SEVERITIES, SEVERITY_PROBS, seed + i);

    forecast.push({
      date: date.toISOString().slice(0, 10),
      day: i + 1,
      predicted_temp_max: parseFloat(temp.toFixed(1)),
      predicted_temp_min: parseFloat((temp - 8).toFixed(1)),
      confidence_lower: parseFloat((temp - 2).toFixed(1)),
      confidence_upper: parseFloat((temp + 2).toFixed(1)),
      heatwave_probability: parseFloat(prob.toFixed(3)),
      is_heatwave: temp >= 40 && prob >= 0.5,
      severity: sev,
      severity_score: SEVERITIES.indexOf(sev) / 4,
    });
  }

  const topShap = [
    { feature: 'temp_max_anomaly',      shap_value: 0.48,  direction: 'increases_risk' },
    { feature: 'consecutive_hot_days',  shap_value: 0.31,  direction: 'increases_risk' },
    { feature: 'heat_index',            shap_value: 0.22,  direction: 'increases_risk' },
    { feature: 'green_cover_pct',       shap_value: -0.14, direction: 'decreases_risk' },
    { feature: 'humidity',              shap_value: -0.09, direction: 'decreases_risk' },
  ];

  return {
    district,
    state: DISTRICTS.find(d => d.name === district)?.state || 'India',
    prediction_date: today.toISOString().slice(0, 10),
    forecast,
    ensemble_confidence: parseFloat((0.6 + seededRandom(seed) * 0.35).toFixed(3)),
    alert_required: baseTemp > 40,
    top_risk_factors: topShap,
    health_risk: {
      total_population: 1048240,
      vulnerable_population: 215000,
      elderly_at_risk: 94000,
      children_at_risk: 121000,
      risk_level: baseTemp > 42 ? 'very_high' : baseTemp > 40 ? 'high' : 'moderate',
      peak_severity: forecast[3].severity,
      peak_date: forecast[3].date,
    },
    cooling_centres: [
      { name: 'Gandhi Hill Community Centre', lat: 16.514, lng: 80.634 },
      { name: 'Municipal Stadium', lat: 16.508, lng: 80.655 },
    ],
    recommended_actions: [
      'Issue public heat advisory',
      'Activate all cooling centres',
      'Alert district health officer',
      'Restrict outdoor labour 12PM-3PM',
    ],
  };
}

export function getMockDistrictRisks() {
  return DISTRICTS.map((d, i) => ({
    ...d,
    district: d.name,
    current_severity: weightedRandom(SEVERITIES, SEVERITY_PROBS, i * 7 + 3),
    max_predicted_temp: parseFloat((36 + seededRandom(i * 3) * 10).toFixed(1)),
    heatwave_probability: parseFloat((0.2 + seededRandom(i * 5) * 0.75).toFixed(2)),
    vulnerable_population: Math.floor(50000 + seededRandom(i * 9) * 500000),
    risk_score: parseFloat((20 + seededRandom(i * 11) * 75).toFixed(1)),
  }));
}

// ── API calls with mock fallback ──────────────────────────────────────────
export async function fetchPrediction(district, state, lat, lng) {
  try {
    const res = await api.post('/predict', { district, state, latitude: lat, longitude: lng });
    return res.data;
  } catch {
    return generateMockForecast(district);
  }
}

export async function fetchDistrictRisks() {
  try {
    const res = await api.get('/predict/districts');
    return res.data;
  } catch {
    return getMockDistrictRisks();
  }
}

export async function fetchWeatherHistory(district, days = 30) {
  try {
    const res = await api.get(`/data/weather/${district}?days=${days}`);
    return res.data.data;
  } catch {
    const today = new Date();
    return Array.from({ length: days }, (_, i) => {
      const d = new Date(today); d.setDate(today.getDate() - (days - i));
      const seed = district.charCodeAt(0) + i;
      const doy = d.getDate() + d.getMonth() * 30;
      const seasonal = 30 + 12 * Math.sin(2 * Math.PI * (doy - 90) / 365);
      return {
        date: d.toISOString().slice(0, 10),
        temp_max: parseFloat((seasonal + (seededRandom(seed) - 0.5) * 5).toFixed(1)),
        temp_min: parseFloat((seasonal - 8 + (seededRandom(seed + 1) - 0.5) * 3).toFixed(1)),
        humidity: parseFloat((55 + (seededRandom(seed + 2) - 0.5) * 20).toFixed(1)),
        heat_index: parseFloat((seasonal + 3 + (seededRandom(seed + 3) - 0.5) * 4).toFixed(1)),
      };
    });
  }
}

export async function fetchExplanation(district) {
  try {
    const res = await api.get(`/explain/${district}`);
    return res.data;
  } catch {
    return {
      district,
      explanation: [
        { feature: 'temp_max_anomaly',     shap_value: 0.48,  direction: 'increases_risk', importance_rank: 1 },
        { feature: 'consecutive_hot_days', shap_value: 0.31,  direction: 'increases_risk', importance_rank: 2 },
        { feature: 'heat_index',           shap_value: 0.22,  direction: 'increases_risk', importance_rank: 3 },
        { feature: 'uhi_score',            shap_value: 0.17,  direction: 'increases_risk', importance_rank: 4 },
        { feature: 'humidity_anomaly',     shap_value: 0.12,  direction: 'increases_risk', importance_rank: 5 },
        { feature: 'green_cover_pct',      shap_value: -0.14, direction: 'decreases_risk', importance_rank: 6 },
        { feature: 'wind_speed',           shap_value: -0.09, direction: 'decreases_risk', importance_rank: 7 },
        { feature: 'pressure_change',      shap_value: 0.07,  direction: 'increases_risk', importance_rank: 8 },
      ],
      base_value: 0.35,
      prediction_value: 0.72,
    };
  }
}

export async function fetchModelMetrics() {
  try {
    const res = await api.get('/data/model-metrics');
    return res.data.models;
  } catch {
    return [
      { name: 'LSTM Forecaster', version: '1.2.0', rmse: 1.83, mae: 1.41, last_trained: '2024-10-15', drift_detected: false, drift_score: 0.04 },
      { name: 'XGBoost Classifier', version: '2.0.1', accuracy: 0.891, f1_score: 0.874, auc_roc: 0.943, last_trained: '2024-10-15', drift_detected: false, drift_score: 0.06 },
      { name: 'Random Forest Severity', version: '1.1.0', accuracy: 0.856, f1_score: 0.841, last_trained: '2024-10-15', drift_detected: false, drift_score: 0.03 },
    ];
  }
}

export const SEVERITY_COLORS = {
  none:     { bg: '#22c55e', text: '#fff', light: '#dcfce7' },
  mild:     { bg: '#eab308', text: '#fff', light: '#fef9c3' },
  moderate: { bg: '#f97316', text: '#fff', light: '#ffedd5' },
  severe:   { bg: '#ef4444', text: '#fff', light: '#fee2e2' },
  extreme:  { bg: '#7c3aed', text: '#fff', light: '#ede9fe' },
};

export { DISTRICTS };
