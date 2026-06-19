from sqlalchemy import Column, BigInteger, String, Boolean, Float, Integer, DateTime, Text, ForeignKey, Date, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
import datetime

from database.connection import Base

class City(Base):
    __tablename__ = "cities"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default="uuid_generate_v4()")
    name = Column(String(255), nullable=False)
    country = Column(String(100), default="India")
    state = Column(String(100))
    bounds = Column(Geometry("POLYGON", srid=4326))
    center_point = Column(Geometry("POINT", srid=4326))
    population = Column(BigInteger)
    area_sqkm = Column(Numeric(10, 2))
    zoom_level = Column(Integer, default=13)
    satellite_source = Column(String(50))
    resolution_m = Column(Numeric(6, 2))
    last_satellite_date = Column(Date)
    last_network_update = Column(DateTime)
    model_version = Column(String(20))
    total_nodes = Column(Integer, default=0)
    total_edges = Column(Integer, default=0)
    avg_centrality = Column(Numeric(5, 4))
    network_resilience_index = Column(Numeric(4, 3))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    nodes = relationship("Node", back_populates="city", cascade="all, delete-orphan")
    edges = relationship("Edge", back_populates="city", cascade="all, delete-orphan")
    stress_tests = relationship("StressTestResult", back_populates="city", cascade="all, delete-orphan")


class Node(Base):
    __tablename__ = "nodes"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    city_id = Column(UUID(as_uuid=True), ForeignKey("cities.id", ondelete="CASCADE"), nullable=False)
    geom = Column(Geometry("POINT", srid=4326), nullable=False)
    longitude = Column(Numeric(11, 8))
    latitude = Column(Numeric(10, 8))
    node_type = Column(String(50), default="intersection")
    is_gateway = Column(Boolean, default=False)
    degree = Column(Integer, default=0)
    betweenness_centrality = Column(Numeric(8, 6), default=0.0)
    closeness_centrality = Column(Numeric(8, 6), default=0.0)
    eigenvector_centrality = Column(Numeric(8, 6), default=0.0)
    criticality_score = Column(Numeric(6, 4), default=0.0)
    criticality_rank = Column(Integer)
    vulnerability_index = Column(Numeric(6, 4), default=0.0)
    connected_component_id = Column(Integer)
    is_isolated = Column(Boolean, default=False)
    name = Column(String(255))
    osm_id = Column(BigInteger)
    tags = Column(JSONB)
    confidence = Column(Numeric(4, 3), default=1.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    city = relationship("City", back_populates="nodes")
    # Relationships for edges
    edges_source = relationship("Edge", foreign_keys="[Edge.source_id]", back_populates="source", cascade="all, delete-orphan")
    edges_target = relationship("Edge", foreign_keys="[Edge.target_id]", back_populates="target", cascade="all, delete-orphan")
    stress_test_removed = relationship("StressTestResult", back_populates="removed_node")


class Edge(Base):
    __tablename__ = "edges"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    city_id = Column(UUID(as_uuid=True), ForeignKey("cities.id", ondelete="CASCADE"), nullable=False)
    source_id = Column(BigInteger, ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False)
    target_id = Column(BigInteger, ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False)
    geom = Column(Geometry("LINESTRING", srid=4326), nullable=False)
    length_meters = Column(Numeric(10, 2))
    road_type = Column(String(50))
    speed_kmh = Column(Integer, default=40)
    one_way = Column(Boolean, default=False)
    flow_criticality = Column(Numeric(6, 4), default=0.0)
    affected_population = Column(Integer, default=0)
    confidence = Column(Numeric(4, 3), default=1.0)
    occlusion_level = Column(Numeric(4, 3), default=0.0)
    name = Column(String(255))
    osm_way_id = Column(BigInteger)
    tags = Column(JSONB)
    is_healing_edge = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    city = relationship("City", back_populates="edges")
    source = relationship("Node", foreign_keys=[source_id], back_populates="edges_source")
    target = relationship("Node", foreign_keys=[target_id], back_populates="edges_target")


class StressTestResult(Base):
    __tablename__ = "stress_test_results"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    city_id = Column(UUID(as_uuid=True), ForeignKey("cities.id", ondelete="CASCADE"), nullable=False)
    test_id = Column(UUID(as_uuid=True), server_default="uuid_generate_v4()")
    removed_node_id = Column(BigInteger, ForeignKey("nodes.id"))
    removed_node_count = Column(Integer, default=1)
    scenario_type = Column(String(50))
    baseline_lcc_size = Column(Integer)
    perturbed_lcc_size = Column(Integer)
    lcc_loss_percent = Column(Numeric(6, 3))
    baseline_avg_path_length = Column(Numeric(8, 4))
    perturbed_avg_path_length = Column(Numeric(8, 4))
    path_increase_factor = Column(Numeric(8, 4))
    baseline_efficiency = Column(Numeric(8, 6))
    perturbed_efficiency = Column(Numeric(8, 6))
    resilience_index = Column(Numeric(6, 4))
    affected_nodes_count = Column(Integer)
    affected_edge_count = Column(Integer)
    critical = Column(Boolean, default=False)
    recommendation_text = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    execution_time_ms = Column(Integer)  # SmallInt in SQL but mapped to Integer here is fine

    city = relationship("City", back_populates="stress_tests")
    removed_node = relationship("Node", back_populates="stress_test_removed")


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    city_id = Column(UUID(as_uuid=True), ForeignKey("cities.id"))
    user_id = Column(String(255))
    action = Column(String(100))
    entity_type = Column(String(50))
    entity_id = Column(BigInteger)
    old_values = Column(JSONB)
    new_values = Column(JSONB)
    ip_address = Column(INET)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
