-- Heatwave Prediction System — Database Initialization
-- This runs automatically when PostgreSQL container starts

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_weather_district_date
    ON weather_observations(district, observed_at DESC);

CREATE INDEX IF NOT EXISTS idx_predictions_district_date
    ON heatwave_predictions(district, prediction_date DESC);

CREATE INDEX IF NOT EXISTS idx_predictions_alert
    ON heatwave_predictions(alert_triggered, created_at DESC);

-- Insert sample district profiles
INSERT INTO district_profiles (district, state, latitude, longitude,
    population, elderly_population_pct, children_population_pct,
    green_cover_pct, water_body_pct, urban_area_pct, hospital_count,
    cooling_centres, health_officer_phone, health_officer_email)
VALUES
    ('Vijayawada', 'Andhra Pradesh', 16.5062, 80.6480,
     1048240, 0.09, 0.17, 0.15, 0.08, 0.72, 47,
     '[{"name":"Gandhi Hill Centre","lat":16.514,"lng":80.634}]',
     '+919440000001', 'health@vijayawada.ap.gov.in'),
    ('Hyderabad', 'Telangana', 17.3850, 78.4867,
     6731790, 0.08, 0.19, 0.12, 0.05, 0.85, 203,
     '[{"name":"GHMC Cooling Centre","lat":17.440,"lng":78.499}]',
     '+919440000002', 'health@hyderabad.tg.gov.in'),
    ('Chennai', 'Tamil Nadu', 13.0827, 80.2707,
     7088000, 0.10, 0.16, 0.11, 0.12, 0.90, 189,
     '[{"name":"Marina Beach Shelter","lat":13.062,"lng":80.277}]',
     '+919440000003', 'health@chennai.tn.gov.in')
ON CONFLICT (district) DO NOTHING;
