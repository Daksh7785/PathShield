import io
import zipfile
import tempfile
import datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from typing import List

from database.connection import get_db
from database.models import City, Node, Edge
from api.routers.analysis import load_graph_from_db
from api.routers.network import get_network_geojson
import shapefile

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

router = APIRouter()


@router.get("/{city_id}/geojson")
async def export_geojson(city_id: str, db: AsyncSession = Depends(get_db)):
    """Export the road network as a GeoJSON file download."""
    geojson_data = await get_network_geojson(city_id, db)
    
    # Return as streaming JSON attachment
    data_io = io.BytesIO(json.dumps(geojson_data, indent=2).encode('utf-8'))
    return StreamingResponse(
        data_io,
        media_type="application/geo+json",
        headers={"Content-Disposition": f"attachment; filename={city_id}_network.geojson"}
    )


@router.post("/{city_id}/report")
async def export_pdf_report(city_id: str, db: AsyncSession = Depends(get_db)):
    """Generate and return a structural vulnerability PDF report."""
    try:
        city_uuid = UUID(city_id)
        stmt = select(City).where(City.id == city_uuid)
    except ValueError:
        stmt = select(City).where(City.name.ilike(city_id))
        
    city_res = await db.execute(stmt)
    city = city_res.scalars().first()
    if not city:
        raise HTTPException(status_code=404, detail="City not found")

    # Fetch top nodes for bottleneck table
    nodes_res = await db.execute(
        select(Node).where(Node.city_id == city.id).order_by(Node.betweenness_centrality.desc()).limit(10)
    )
    top_nodes = nodes_res.scalars().all()

    # Generate PDF in memory
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'ReportTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor('#002b49'),
        spaceAfter=12
    )
    section_style = ParagraphStyle(
        'ReportSection',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=colors.HexColor('#002b49'),
        spaceBefore=18,
        spaceAfter=8
    )
    body_style = ParagraphStyle(
        'ReportBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#333333'),
        spaceAfter=8
    )

    # 1. Cover Page
    story.append(Paragraph("ROUTE RESILIENCE ASSESSMENT REPORT", title_style))
    story.append(Paragraph(f"Target City: {city.name}, {city.state}", ParagraphStyle('Subtitle', parent=styles['Normal'], fontSize=12, spaceAfter=20)))
    story.append(Spacer(1, 20))
    story.append(Paragraph(f"Generated Date: {datetime.date.today().strftime('%B %d, %Y')}", body_style))
    
    resilience_val = float(city.network_resilience_index) if city.network_resilience_index else 1.0
    status_text = "VULNERABLE (RED)" if resilience_val < 0.5 else "CRITICAL (YELLOW)" if resilience_val < 0.7 else "RESILIENT (GREEN)"
    story.append(Paragraph(f"Overall Network Resilience Rating: <b>{resilience_val:.2f} ({status_text})</b>", body_style))
    story.append(Spacer(1, 20))
    story.append(PageBreak())

    # 2. Section 1: Overview
    story.append(Paragraph("1. Infrastructure Network Overview", section_style))
    overview_text = (
        f"This section details the topological road asset layout of {city.name} derived from ISRO EO satellites. "
        f"The network comprises a total of {city.total_nodes:,} intersections (nodes) and {city.total_edges:,} connecting road segments (edges). "
        f"Downstream GIS routing calculations use projected coordinates for metric precision."
    )
    story.append(Paragraph(overview_text, body_style))

    # 3. Section 2: Bottlenecks
    story.append(Paragraph("2. Top 10 Bottleneck Intersections (Gatekeeper Nodes)", section_style))
    
    table_data = [["Rank", "Node ID", "Longitude", "Latitude", "Centrality"]]
    for rank, node in enumerate(top_nodes):
        table_data.append([
            str(rank + 1),
            str(node.id),
            f"{float(node.longitude):.6f}",
            f"{float(node.latitude):.6f}",
            f"{float(node.betweenness_centrality):.6f}"
        ])
        
    t = Table(table_data, colWidths=[40, 80, 100, 100, 100])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#002b49')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#f2f2f2')),
        ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#cccccc')),
        ('FONTSIZE', (0,0), (-1,-1), 9),
    ]))
    story.append(t)
    story.append(Spacer(1, 20))

    # 4. Section 3: Recommendations
    story.append(Paragraph("3. Recommendations & Vulnerability Hardening", section_style))
    recommendations = [
        "1. Prioritize structural reinforcement and concrete drainage overlays around the top-ranked bottleneck nodes to prevent flood blockages.",
        "2. Build parallel bypass connectors or secondary lanes within 500m of gatekeeper nodes to distribute traffic loads during closures.",
        "3. Integrate real-time alternate routing triggers on the municipal transport bus feeds when primary corridors suffer delays."
    ]
    for rec in recommendations:
        story.append(Paragraph(rec, body_style))

    doc.build(story)
    
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={city.name.lower()}_resilience_report.pdf"}
    )


@router.get("/{city_id}/shapefile")
async def export_shapefile(city_id: str, db: AsyncSession = Depends(get_db)):
    """Export road network layers as a zipped ESRI Shapefile (.shp, .shx, .dbf)."""
    try:
        city_uuid = UUID(city_id)
        stmt = select(City).where(City.id == city_uuid)
    except ValueError:
        stmt = select(City).where(City.name.ilike(city_id))
        
    city_res = await db.execute(stmt)
    city = city_res.scalars().first()
    if not city:
        raise HTTPException(status_code=404, detail="City not found")

    # Fetch nodes and edges
    nodes_res = await db.execute(select(Node).where(Node.city_id == city.id))
    nodes = nodes_res.scalars().all()
    edges_res = await db.execute(select(Edge).where(Edge.city_id == city.id))
    edges = edges_res.scalars().all()

    # Create temporary zip archive
    temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    zip_path = temp_zip.name
    temp_zip.close()

    with zipfile.ZipFile(zip_path, 'w') as zf:
        # 1. Write Nodes Shapefile
        with tempfile.TemporaryDirectory() as temp_dir:
            node_shp_path = os.path.join(temp_dir, "nodes")
            w = shapefile.Writer(node_shp_path, shapefile.POINT)
            w.field("ID", "N")
            w.field("TYPE", "C", size=50)
            w.field("CENTRALITY", "F", decimal=6)
            
            for n in nodes:
                w.point(float(n.longitude), float(n.latitude))
                w.record(int(n.id), n.node_type, float(n.betweenness_centrality))
            w.close()
            
            # Zip all generated files (.shp, .shx, .dbf)
            for ext in [".shp", ".shx", ".dbf"]:
                zf.write(node_shp_path + ext, arcname="nodes" + ext)

        # 2. Write Edges Shapefile
        with tempfile.TemporaryDirectory() as temp_dir:
            edge_shp_path = os.path.join(temp_dir, "edges")
            w = shapefile.Writer(edge_shp_path, shapefile.POLYLINE)
            w.field("ID", "N")
            w.field("SRC", "N")
            w.field("TGT", "N")
            w.field("LEN_M", "F", decimal=2)
            w.field("HEALED", "L")
            
            for e in edges:
                # Get coordinates
                coords = []
                try:
                    from shapely import wkb
                    geom_shape = wkb.loads(bytes(e.geom.data))
                    coords = list(geom_shape.coords)
                except Exception:
                    src_node = next((n for n in nodes if n.id == e.source_id), None)
                    tgt_node = next((n for n in nodes if n.id == e.target_id), None)
                    if src_node and tgt_node:
                        coords = [
                            [float(src_node.longitude), float(src_node.latitude)],
                            [float(tgt_node.longitude), float(tgt_node.latitude)]
                        ]
                
                if coords:
                    w.line([[[float(coord[0]), float(coord[1])] for coord in coords]])
                    w.record(int(e.id), int(e.source_id), int(e.target_id), float(e.length_meters), int(e.is_healing_edge))
            w.close()
            
            for ext in [".shp", ".shx", ".dbf"]:
                zf.write(edge_shp_path + ext, arcname="edges" + ext)

    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename=f"{city.name.lower()}_shapefiles.zip"
    )
import json
