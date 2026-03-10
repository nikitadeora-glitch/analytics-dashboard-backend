-- Add Event table for custom event tracking
-- Run this directly on your database

CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    visit_id INTEGER REFERENCES visits(id),
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB,
    url VARCHAR(500),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS ix_events_id ON events(id);
CREATE INDEX IF NOT EXISTS ix_events_visit_id ON events(visit_id);
CREATE INDEX IF NOT EXISTS ix_events_event_type ON events(event_type);
CREATE INDEX IF NOT EXISTS ix_events_timestamp ON events(timestamp);
