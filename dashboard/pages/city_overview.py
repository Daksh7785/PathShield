"""City overview page with interactive Folium map."""
import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import yaml

API_BASE = "http://localhost:8000/api/v1"

def get_city_stats(city_id: str) -> dict:
    try:
        r = requests.get(f"{API_BASE}/cities/{city_id}", timeout=5)
        return r.json() if r.status_code == 200 else {}
    except:
        return {}

def get_network_geojson(city_id: str) -> dict:
    try:
        r = requests.get(f"{API_BASE}/network/{city_id}/geojson", timeout=10)
        return r.json() if r.status_code == 200 else {"type": "FeatureCollection", "features": []}
    except:
        return {"type": "FeatureCollection", "features": []}

def criticality_color(score: float) -> str:
    """Map centrality score [0,1] to color string."""
    if score > 0.7:
        return "#ff3333"
    elif score > 0.4:
        return "#ff9900"
    elif score > 0.2:
        return "#ffcc00"
    else:
        return "#00cc66"

def render():
    st.title("🏙️ City Overview")
    
    # Load city config
    with open("configs/cities.yaml") as f:
        cities_config = yaml.safe_load(f)
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.subheader("Select City")
        city_key = st.selectbox(
            "City",
            options=list(cities_config["cities"].keys()),
            format_func=lambda k: cities_config["cities"][k]["name"],
            label_visibility="collapsed"
        )
        city = cities_config["cities"][city_key]
        
        st.divider()
        
        # Layer controls
        st.subheader("Layers")
        show_roads = st.checkbox("Road network", value=True)
        show_heatmap = st.checkbox("Criticality heatmap", value=True)
        
        st.divider()
        
        # Stats
        stats = get_city_stats(city_key)
        if stats:
            st.metric("Total intersections", f"{stats.get('total_nodes', 0):,}")
            st.metric("Road segments", f"{stats.get('total_edges', 0):,}")
            st.metric("Network resilience", f"{stats.get('network_resilience_index', 0):.2f}")
    
    with col2:
        # Build Folium map
        m = folium.Map(
            location=[city["center_lat"], city["center_lng"]],
            zoom_start=city["zoom_level"],
            tiles="CartoDB dark_matter",
        )
        
        if show_roads or show_heatmap:
            geojson = get_network_geojson(city_key)
            
            if geojson["features"]:
                # Road network layer
                if show_roads:
                    folium.GeoJson(
                        {
                            "type": "FeatureCollection",
                            "features": [f for f in geojson["features"]
                                         if f["geometry"]["type"] == "LineString"]
                        },
                        style_function=lambda f: {
                            "color": "#4488ff",
                            "weight": 1.5,
                            "opacity": 0.7,
                        },
                        name="Roads",
                    ).add_to(m)
                
                # Criticality heatmap layer
                if show_heatmap:
                    node_features = [f for f in geojson["features"]
                                     if f["geometry"]["type"] == "Point"]
                    
                    for feat in node_features[:500]:  # Limit for performance
                        props = feat["properties"]
                        score = props.get("betweenness_centrality", 0)
                        if score < 0.05:
                            continue  # Skip low-criticality nodes
                        
                        color = criticality_color(score)
                        lat = feat["geometry"]["coordinates"][1]
                        lng = feat["geometry"]["coordinates"][0]
                        
                        folium.CircleMarker(
                            location=[lat, lng],
                            radius=max(4, score * 20),
                            color=color,
                            fill=True,
                            fill_color=color,
                            fill_opacity=0.8,
                            popup=folium.Popup(
                                f"""<b>Node {props.get('id', '')}</b><br>
                                Type: {props.get('node_type', 'unknown')}<br>
                                Centrality: {score:.4f}<br>
                                Degree: {props.get('degree', 0)}<br>
                                Rank: #{props.get('criticality_rank', 'N/A')}""",
                                max_width=200
                            ),
                        ).add_to(m)
            else:
                # Demo: show synthetic data message
                folium.Marker(
                    [city["center_lat"], city["center_lng"]],
                    popup="Run inference pipeline to load road network",
                    icon=folium.Icon(color="blue", icon="info-sign"),
                ).add_to(m)
        
        # Legend
        legend_html = """
        <div style="position: fixed; bottom: 30px; right: 30px; 
                    background: rgba(0,0,0,0.8); padding: 12px; border-radius: 8px;
                    color: white; font-size: 12px; z-index: 1000;">
            <b>Criticality</b><br>
            🔴 High (&gt;0.7)<br>
            🟠 Medium (0.4–0.7)<br>
            🟡 Low (0.2–0.4)<br>
            🟢 Minimal (&lt;0.2)
        </div>
        """
        m.get_root().html.add_child(folium.Element(legend_html))
        
        st_folium(m, width="100%", height=550)
