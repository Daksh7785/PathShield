-- Enable PostGIS extensions for spatial calculations
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- Multi-Tenant Organizations Registry
CREATE TABLE IF NOT EXISTS organizations (
    id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    api_key VARCHAR(255) UNIQUE NOT NULL,
    daily_quota_limit INTEGER DEFAULT 10000,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Administrative Bounding Regions
CREATE TABLE IF NOT EXISTS cities (
    id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    country VARCHAR(100) NOT NULL,
    population INTEGER,
    satellite_source VARCHAR(100),
    geom GEOMETRY(Polygon, 4326),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Topological Graph Intersections
CREATE TABLE IF NOT EXISTS nodes (
    id BIGINT PRIMARY KEY,
    city_id VARCHAR(100) REFERENCES cities(id) ON DELETE CASCADE,
    node_type VARCHAR(50) DEFAULT 'intersection',
    betweenness_centrality DOUBLE PRECISION DEFAULT 0.0,
    closeness_centrality DOUBLE PRECISION DEFAULT 0.0,
    is_gateway BOOLEAN DEFAULT FALSE,
    geom GEOMETRY(Point, 4326) NOT NULL
);

-- Centerline Road Network Vectors
CREATE TABLE IF NOT EXISTS links (
    source BIGINT REFERENCES nodes(id) ON DELETE CASCADE,
    target BIGINT REFERENCES nodes(id) ON DELETE CASCADE,
    city_id VARCHAR(100) REFERENCES cities(id) ON DELETE CASCADE,
    length_meters DOUBLE PRECISION NOT NULL,
    confidence DOUBLE PRECISION DEFAULT 1.0,
    is_healing_edge BOOLEAN DEFAULT FALSE,
    geom GEOMETRY(LineString, 4326) NOT NULL,
    PRIMARY KEY (source, target)
);

-- Active Disaster Zones (NASAFIRMS/GDACS)
CREATE TABLE IF NOT EXISTS active_hazards (
    id SERIAL PRIMARY KEY,
    scenario_type VARCHAR(100) NOT NULL, -- 'flood', 'wildfire', 'earthquake'
    radius_meters DOUBLE PRECISION NOT NULL,
    geom GEOMETRY(Polygon, 4326) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create Spatial GIST Indexes for performance
CREATE INDEX IF NOT EXISTS idx_cities_geom ON cities USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_nodes_geom ON nodes USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_links_geom ON links USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_hazards_geom ON active_hazards USING GIST (geom);
