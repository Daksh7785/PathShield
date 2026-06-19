import os
import uuid
import datetime
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/routeresilience")

# Base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# We try to create the async engine for Postgres.
# If it fails or is offline at query time, get_db automatically switches to a MockSession.
try:
    engine = create_async_engine(DATABASE_URL, echo=False, pool_size=10, max_overflow=20)
    AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
except Exception as e:
    engine = None
    AsyncSessionLocal = None


# =====================================================================
# IN-MEMORY RESILIENT DATABASE BACKEND (FOR OFFLINE / ZERO-CONFIG DEPLOYMENTS)
# =====================================================================

class MockScalars:
    def __init__(self, data_list):
        self.data_list = data_list

    def all(self):
        return self.data_list

    def first(self):
        return self.data_list[0] if self.data_list else None


class MockResult:
    def __init__(self, data_list):
        self.data_list = data_list

    def scalars(self):
        return MockScalars(self.data_list)


class MockSession:
    """Zero-dependency, in-memory SQLAlchemy session simulator."""
    def __init__(self):
        self._initialize_mock_db()

    def _initialize_mock_db(self):
        from database.models import City, Node, Edge
        
        # Static IDs to preserve relationships
        self.bengaluru_id = uuid.UUID("a889fa6e-21bb-49ea-88f2-8924f9fa2772")
        self.delhi_id = uuid.UUID("b778fa6e-21bb-49ea-88f2-8924f9fa2773")

        # Mock Cities
        self.cities = [
            City(
                id=self.bengaluru_id,
                name="Bengaluru",
                state="Karnataka",
                country="India",
                population=12000000,
                area_sqkm=741.0,
                zoom_level=13,
                satellite_source="Cartosat-3",
                resolution_m=0.28,
                total_nodes=500,
                total_edges=800,
                avg_centrality=0.145,
                network_resilience_index=0.825
            ),
            City(
                id=self.delhi_id,
                name="Delhi",
                state="Delhi",
                country="India",
                population=16000000,
                area_sqkm=1484.0,
                zoom_level=13,
                satellite_source="Sentinel-2",
                resolution_m=10.0,
                total_nodes=120,
                total_edges=210,
                avg_centrality=0.112,
                network_resilience_index=0.785
            )
        ]

        # Mock Nodes (grid of 100 intersections for Bengaluru map rendering)
        self.nodes = []
        for i in range(1, 11):
            for j in range(1, 11):
                node_id = i * 10 + j
                self.nodes.append(Node(
                    id=node_id,
                    city_id=self.bengaluru_id,
                    longitude=77.59 + (j * 0.01),
                    latitude=12.97 + (i * 0.01),
                    node_type="intersection" if (i != j) else "endpoint",
                    degree=2,
                    betweenness_centrality=0.05,
                    closeness_centrality=0.04,
                    is_gateway=(i == 5 and j == 5),
                    geom=None
                ))

        # Mock Edges (grid connections)
        self.edges = []
        edge_idx = 1
        for i in range(1, 11):
            for j in range(1, 11):
                n1 = i * 10 + j
                # Horizontal connection
                if j < 10:
                    n2 = i * 10 + (j + 1)
                    self.edges.append(Edge(
                        id=edge_idx,
                        city_id=self.bengaluru_id,
                        source_id=n1,
                        target_id=n2,
                        length_meters=1100.0,
                        is_healing_edge=False,
                        confidence=1.0,
                        geom=None
                    ))
                    edge_idx += 1
                # Vertical connection
                if i < 10:
                    n3 = (i + 1) * 10 + j
                    self.edges.append(Edge(
                        id=edge_idx,
                        city_id=self.bengaluru_id,
                        source_id=n1,
                        target_id=n3,
                        length_meters=1100.0,
                        is_healing_edge=False,
                        confidence=1.0,
                        geom=None
                    ))
                    edge_idx += 1

        self.stress_tests = []
        self.audit_logs = []

    async def execute(self, statement, *args, **kwargs):
        stmt_str = str(statement).lower()
        
        # Querying cities
        if "from cities" in stmt_str or "cities." in stmt_str:
            if "cities.id = :" in stmt_str or "cities.id =" in stmt_str:
                # Find by ID
                try:
                    val = statement.compile().params.get("id_1") or statement.compile().params.get("param_1")
                    if isinstance(val, str):
                        val = uuid.UUID(val)
                    res = [c for c in self.cities if c.id == val]
                    return MockResult(res)
                except Exception:
                    pass
            if "like" in stmt_str or "name" in stmt_str:
                # Find by name ilike
                try:
                    name_param = statement.compile().params.get("name_1") or "%bengaluru%"
                    clean_name = str(name_param).replace("%", "").lower()
                    res = [c for c in self.cities if clean_name in c.name.lower()]
                    return MockResult(res)
                except Exception:
                    pass
            return MockResult(self.cities)

        # Querying nodes
        elif "from nodes" in stmt_str or "nodes." in stmt_str:
            city_id = None
            try:
                city_id = statement.compile().params.get("city_id_1")
                if isinstance(city_id, str):
                    city_id = uuid.UUID(city_id)
            except Exception:
                pass
                
            if city_id:
                res = [n for n in self.nodes if n.city_id == city_id]
                return MockResult(res)
            return MockResult(self.nodes)

        # Querying edges/links
        elif "from edges" in stmt_str or "edges." in stmt_str:
            city_id = None
            try:
                city_id = statement.compile().params.get("city_id_1")
                if isinstance(city_id, str):
                    city_id = uuid.UUID(city_id)
            except Exception:
                pass
                
            if city_id:
                res = [e for e in self.edges if e.city_id == city_id]
                return MockResult(res)
            return MockResult(self.edges)

        # Default fallback (empty list)
        return MockResult([])

    def add(self, instance):
        from database.models import StressTestResult, AuditLog
        if isinstance(instance, StressTestResult):
            self.stress_tests.append(instance)
        elif isinstance(instance, AuditLog):
            self.audit_logs.append(instance)

    async def flush(self):
        pass

    async def commit(self):
        pass

    async def rollback(self):
        pass

    async def close(self):
        pass


# =====================================================================
# API / SERVICE DEPENDENCY INTERFACE
# =====================================================================

async def get_db():
    """
    Get database session context.
    Automatically tests Postgres availability, falling back to a MockSession
    if the connection fails or is not configured.
    """
    if engine is None or AsyncSessionLocal is None:
        print("✓ Database: Postgres offline. Using in-memory fallback session.")
        yield MockSession()
        return

    # Check connection health
    use_fallback = False
    try:
        # Fast query timeout check
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as e:
        print(f"⚠ Database: Postgres connection failed ({e}). Falling back to in-memory session.")
        use_fallback = True

    if use_fallback:
        yield MockSession()
        return

    # Connection OK, yield normal session
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
