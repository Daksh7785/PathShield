-- Enable extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- CITIES
-- ============================================================
CREATE TABLE IF NOT EXISTS cities (
     id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
     name VARCHAR(255) NOT NULL,
     country VARCHAR(100) DEFAULT 'India',
     state VARCHAR(100),
     bounds GEOMETRY(POLYGON, 4326),
     center_point GEOMETRY(POINT, 4326),
     population BIGINT,
     area_sqkm DECIMAL(10,2),
     zoom_level SMALLINT DEFAULT 13,
     satellite_source VARCHAR(50),
     resolution_m DECIMAL(6,2),
     last_satellite_date DATE,
     last_network_update TIMESTAMP,
     model_version VARCHAR(20),
     total_nodes INTEGER DEFAULT 0,
     total_edges INTEGER DEFAULT 0,
     avg_centrality DECIMAL(5,4),
     network_resilience_index DECIMAL(4,3),
     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
     updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
     CONSTRAINT city_name_unique UNIQUE (name, country)
);
CREATE INDEX IF NOT EXISTS idx_cities_bounds ON cities USING GIST(bounds);
CREATE INDEX IF NOT EXISTS idx_cities_center ON cities USING GIST(center_point);

-- ============================================================
-- NODES (Intersections & Endpoints)
-- ============================================================
CREATE TABLE IF NOT EXISTS nodes (
     id BIGSERIAL PRIMARY KEY,
     city_id UUID NOT NULL REFERENCES cities(id) ON DELETE CASCADE,
     geom GEOMETRY(POINT, 4326) NOT NULL,
     longitude DECIMAL(11,8),
     latitude DECIMAL(10,8),
     node_type VARCHAR(50) DEFAULT 'intersection',
     is_gateway BOOLEAN DEFAULT FALSE,
     degree INTEGER DEFAULT 0,
     betweenness_centrality DECIMAL(8,6) DEFAULT 0,
     closeness_centrality DECIMAL(8,6) DEFAULT 0,
     eigenvector_centrality DECIMAL(8,6) DEFAULT 0,
     criticality_score DECIMAL(6,4) DEFAULT 0,
     criticality_rank INTEGER,
     vulnerability_index DECIMAL(6,4) DEFAULT 0,
     connected_component_id INTEGER,
     is_isolated BOOLEAN DEFAULT FALSE,
     name VARCHAR(255),
     osm_id BIGINT,
     tags JSONB,
     confidence DECIMAL(4,3) DEFAULT 1.0,
     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
     updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
     CONSTRAINT node_city_unique UNIQUE (city_id, longitude, latitude)
);
CREATE INDEX IF NOT EXISTS idx_nodes_geom ON nodes USING GIST(geom);
CREATE INDEX IF NOT EXISTS idx_nodes_betweenness ON nodes(betweenness_centrality DESC);
CREATE INDEX IF NOT EXISTS idx_nodes_city ON nodes(city_id);
CREATE INDEX IF NOT EXISTS idx_nodes_gateway ON nodes(is_gateway) WHERE is_gateway = TRUE;
CREATE INDEX IF NOT EXISTS idx_nodes_criticality ON nodes(city_id, betweenness_centrality DESC);

-- ============================================================
-- EDGES (Road Segments)
-- ============================================================
CREATE TABLE IF NOT EXISTS edges (
     id BIGSERIAL PRIMARY KEY,
     city_id UUID NOT NULL REFERENCES cities(id) ON DELETE CASCADE,
     source_id BIGINT NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
     target_id BIGINT NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
     geom GEOMETRY(LINESTRING, 4326) NOT NULL,
     length_meters DECIMAL(10,2),
     road_type VARCHAR(50),
     speed_kmh SMALLINT DEFAULT 40,
     one_way BOOLEAN DEFAULT FALSE,
     flow_criticality DECIMAL(6,4) DEFAULT 0,
     affected_population INTEGER DEFAULT 0,
     confidence DECIMAL(4,3) DEFAULT 1.0,
     occlusion_level DECIMAL(4,3) DEFAULT 0,
     name VARCHAR(255),
     osm_way_id BIGINT,
     tags JSONB,
     is_healing_edge BOOLEAN DEFAULT FALSE,
     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
     updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
     CONSTRAINT edges_no_self_loop CHECK (source_id != target_id)
);
CREATE INDEX IF NOT EXISTS idx_edges_geom ON edges USING GIST(geom);
CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source_id);
CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target_id);
CREATE INDEX IF NOT EXISTS idx_edges_city ON edges(city_id);
CREATE INDEX IF NOT EXISTS idx_edges_criticality ON edges(flow_criticality DESC);

-- ============================================================
-- STRESS TEST RESULTS
-- ============================================================
CREATE TABLE IF NOT EXISTS stress_test_results (
     id BIGSERIAL PRIMARY KEY,
     city_id UUID NOT NULL REFERENCES cities(id) ON DELETE CASCADE,
     test_id UUID DEFAULT uuid_generate_v4(),
     removed_node_id BIGINT REFERENCES nodes(id),
     removed_node_count INTEGER DEFAULT 1,
     scenario_type VARCHAR(50),
     baseline_lcc_size INTEGER,
     perturbed_lcc_size INTEGER,
     lcc_loss_percent DECIMAL(6,3),
     baseline_avg_path_length DECIMAL(8,4),
     perturbed_avg_path_length DECIMAL(8,4),
     path_increase_factor DECIMAL(8,4),
     baseline_efficiency DECIMAL(8,6),
     perturbed_efficiency DECIMAL(8,6),
     resilience_index DECIMAL(6,4),
     affected_nodes_count INTEGER,
     affected_edge_count INTEGER,
     critical BOOLEAN DEFAULT FALSE,
     recommendation_text TEXT,
     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
     execution_time_ms SMALLINT
);
CREATE INDEX IF NOT EXISTS idx_stress_city ON stress_test_results(city_id);
CREATE INDEX IF NOT EXISTS idx_stress_node ON stress_test_results(removed_node_id);
CREATE INDEX IF NOT EXISTS idx_stress_resilience ON stress_test_results(resilience_index);

-- ============================================================
-- AUDIT LOG
-- ============================================================
CREATE TABLE IF NOT EXISTS audit_log (
     id BIGSERIAL PRIMARY KEY,
     city_id UUID REFERENCES cities(id),
     user_id VARCHAR(255),
     action VARCHAR(100),
     entity_type VARCHAR(50),
     entity_id BIGINT,
     old_values JSONB,
     new_values JSONB,
     ip_address INET,
     timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_city ON audit_log(city_id);

-- ============================================================
-- MATERIALIZED VIEW — Network Stats
-- ============================================================
CREATE MATERIALIZED VIEW IF NOT EXISTS network_stats_mv AS
SELECT
     c.id AS city_id,
     c.name AS city_name,
     COUNT(DISTINCT n.id) AS node_count,
     COUNT(DISTINCT e.id) AS edge_count,
     AVG(n.betweenness_centrality) AS avg_centrality,
     MAX(n.betweenness_centrality) AS max_centrality,
     PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY n.betweenness_centrality) AS p95_centrality,
     COUNT(DISTINCT n.id) FILTER (WHERE n.is_gateway) AS gateway_node_count,
     COALESCE(SUM(e.length_meters), 0) AS total_road_length_m,
     CURRENT_TIMESTAMP AS last_updated
FROM cities c
LEFT JOIN nodes n ON c.id = n.city_id
LEFT JOIN edges e ON c.id = e.city_id
GROUP BY c.id, c.name;

CREATE UNIQUE INDEX IF NOT EXISTS idx_network_stats_city ON network_stats_mv(city_id);

-- ============================================================
-- SEED: Insert sample cities
-- ============================================================
INSERT INTO cities (name, state, country, center_point, bounds, population, area_sqkm, zoom_level, satellite_source, resolution_m)
VALUES
   ('Bengaluru', 'Karnataka', 'India',
    ST_SetSRID(ST_MakePoint(77.5946, 12.9716), 4326),
    ST_SetSRID(ST_MakeEnvelope(77.45, 12.85, 77.75, 13.10, 4326), 4326),
    12000000, 741.0, 13, 'cartosat3', 0.5),
   ('Mumbai', 'Maharashtra', 'India',
    ST_SetSRID(ST_MakePoint(72.8777, 19.0760), 4326),
    ST_SetSRID(ST_MakeEnvelope(72.77, 18.89, 72.99, 19.28, 4326), 4326),
    20700000, 603.0, 12, 'resourcesat_liss4', 5.8),
   ('Delhi', 'Delhi', 'India',
    ST_SetSRID(ST_MakePoint(77.2090, 28.6139), 4326),
    ST_SetSRID(ST_MakeEnvelope(76.84, 28.40, 77.35, 28.88, 4326), 4326),
    32000000, 1484.0, 11, 'sentinel2', 10.0)
ON CONFLICT (name, country) DO NOTHING;
