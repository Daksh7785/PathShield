"""Stress testing simulation page."""
import streamlit as st
import requests
import yaml
import plotly.graph_objects as go

API_BASE = "http://localhost:8000/api/v1"

def run_ablation_api(city_id: str, payload: dict) -> dict:
    try:
        r = requests.post(f"{API_BASE}/analysis/{city_id}/stress-test", json=payload, timeout=15)
        return r.json() if r.status_code == 200 else {}
    except:
        return {}

def fetch_top_nodes(city_id: str) -> list:
    try:
        r = requests.get(f"{API_BASE}/network/{city_id}/nodes?limit=30", timeout=5)
        return r.json() if r.status_code == 200 else []
    except:
        return []

def render():
    st.title("⚡ Structural Stress Testing")
    
    with open("configs/cities.yaml") as f:
        cities_config = yaml.safe_load(f)
        
    city_key = st.selectbox(
        "Select Target City",
        options=list(cities_config["cities"].keys()),
        format_func=lambda k: cities_config["cities"][k]["name"],
        key="stress_city"
    )
    
    mode = st.selectbox(
        "Ablation Scenario Type",
        ["Single node removal", "Flood zone simulation", "Cascading failure", "Random failure"]
    )
    
    payload = {}
    
    if mode == "Single node removal":
        top_nodes = fetch_top_nodes(city_key)
        node_options = [x["id"] for x in top_nodes]
        
        if not node_options:
            node_options = [1, 2, 3, 4, 5] # Fallbacks
            
        selected_nodes = st.multiselect("Select nodes to disable/remove", node_options, default=node_options[:1])
        payload = {
            "scenario_type": "equipment_failure",
            "removed_node_ids": selected_nodes
        }
    elif mode == "Flood zone simulation":
        st.caption("Provide rectangular bounds representing flooded zone [minx, miny, maxx, maxy]")
        minx = st.number_input("Min X (Longitude)", value=77.55, format="%.4f")
        miny = st.number_input("Min Y (Latitude)", value=12.90, format="%.4f")
        maxx = st.number_input("Max X (Longitude)", value=77.65, format="%.4f")
        maxy = st.number_input("Max Y (Latitude)", value=13.00, format="%.4f")
        payload = {
            "scenario_type": "flood",
            "flood_bounds": [minx, miny, maxx, maxy]
        }
    elif mode == "Cascading failure":
        seed = st.number_input("Initial Seed Node ID to disable", value=1, step=1)
        payload = {
            "scenario_type": "peak_traffic", # simulates cascading on busiest components
            "removed_node_ids": [seed]
        }
    else:
        prob = st.slider("Node failure probability", 0.01, 0.50, 0.10)
        payload = {
            "scenario_type": "peak_traffic",
            "radius": prob # mapped parameter
        }
        
    if st.button("▶ Run Stress Test"):
        with st.spinner("Executing simulation..."):
            res = run_ablation_api(city_key, payload)
            
        if not res:
            st.error("Simulation failed. Make sure the database has been seeded and the API is running.")
            return
            
        # Metrics panels
        col1, col2, col3 = st.columns(3)
        
        res_idx = res.get("resilience_index", 1.0)
        color = "🟢 Safe" if res_idx >= 0.8 else "🟡 High Risk" if res_idx >= 0.5 else "🔴 Critical"
        
        with col1:
            st.metric("Resilience Index Score", f"{res_idx:.3f}", delta=color)
        with col2:
            st.metric("LCC Connectivity Loss", f"{res.get('lcc_loss_percent', 0.0):.2f}%")
        with col3:
            detour_val = res.get('path_increase_factor', 1.0)
            st.metric("Path Detour Factor", f"{detour_val:.2f}x" if detour_val != 999.0 else "INF")
            
        st.subheader("Planning Guidelines")
        st.warning(res.get("recommendation", "Monitor infrastructure regular cycles."))
        
        # Download reports
        st.divider()
        st.subheader("Export Results")
        
        col_pdf, col_json = st.columns(2)
        with col_pdf:
            # Trigger report build
            try:
                pdf_url = f"{API_BASE}/export/{city_key}/report"
                pdf_data = requests.post(pdf_url, timeout=10).content
                st.download_button(
                    "📥 Download PDF Vulnerability Report",
                    data=pdf_data,
                    file_name=f"{city_key}_resilience_report.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.caption(f"PDF generation offline: {e}")
                
        with col_json:
            try:
                geojson_url = f"{API_BASE}/export/{city_key}/geojson"
                geojson_data = requests.get(geojson_url, timeout=10).content
                st.download_button(
                    "📥 Export Network GeoJSON Layers",
                    data=geojson_data,
                    file_name=f"{city_key}_network.geojson",
                    mime="application/json"
                )
            except Exception as e:
                st.caption(f"GeoJSON export offline: {e}")
