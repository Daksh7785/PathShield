"""Disaster scenarios mapping and simulation page."""
import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import yaml

API_BASE = "http://localhost:8000/api/v1"

def run_scenario_api(city_id: str, scenario: str, payload: dict) -> dict:
    # Trigger scenario
    try:
        r = requests.post(f"{API_BASE}/analysis/{city_id}/stress-test", json={
            "scenario_type": scenario,
            **payload
        }, timeout=15)
        return r.json() if r.status_code == 200 else {}
    except:
        return {}

def render():
    st.title("🌊 Disaster Simulation & Evacuation Planning")
    
    with open("configs/cities.yaml") as f:
        cities_config = yaml.safe_load(f)
        
    city_key = st.selectbox(
        "Select City Profile",
        options=list(cities_config["cities"].keys()),
        format_func=lambda k: cities_config["cities"][k]["name"],
        key="disaster_city"
    )
    city = cities_config["cities"][city_key]
    
    scenario = st.selectbox(
        "Select Disaster Profile",
        ["Flood Inundation", "Radial Earthquake Damage", "Peak Traffic overloading"]
    )
    
    payload = {}
    if scenario == "Flood Inundation":
        st.write("Simulate flooding (disables all intersections within bounds)")
        minx = st.number_input("Min X (Long)", value=77.5500, format="%.4f")
        miny = st.number_input("Min Y (Lat)", value=12.9000, format="%.4f")
        maxx = st.number_input("Max X (Long)", value=77.6000, format="%.4f")
        maxy = st.number_input("Max Y (Lat)", value=12.9500, format="%.4f")
        payload = {"flood_bounds": [minx, miny, maxx, maxy]}
        sc_type = "flood"
    elif scenario == "Radial Earthquake Damage":
        st.write("Radial damage (epicenter and degree radius)")
        ex = st.number_input("Epicenter Longitude", value=city["center_lng"], format="%.4f")
        ey = st.number_input("Epicenter Latitude", value=city["center_lat"], format="%.4f")
        radius = st.slider("Damage radius (degrees)", 0.005, 0.04, 0.015, step=0.005)
        payload = {"epicenter": [ex, ey], "radius": radius}
        sc_type = "earthquake"
    else:
        st.write("Overload the top 20% highest centrality intersections")
        payload = {}
        sc_type = "peak_traffic"

    if st.button("Simulate Impact"):
        with st.spinner("Simulating disaster impact..."):
            res = run_scenario_api(city_key, sc_type, payload)
            
        if not res:
            st.error("Simulation engine failed to compute. Verify API is running.")
            return
            
        st.subheader("Disaster Impact Assessment")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Disrupted Intersections", f"{res.get('affected_nodes_count', 0)}")
        with col2:
            st.metric("Resilience Rating", f"{res.get('resilience_index', 1.0):.3f}")
        with col3:
            st.metric("LCC Loss %", f"{res.get('lcc_loss_percent', 0.0):.2f}%")
            
        st.subheader("Evacuation Guidelines")
        st.info(res.get("recommendation", "Execute standard emergency response protocols."))

        # Map display
        m = folium.Map(
            location=[city["center_lat"], city["center_lng"]],
            zoom_start=city["zoom_level"],
            tiles="CartoDB dark_matter",
        )
        
        # Draw search area visual helper
        if sc_type == "flood":
            folium.Rectangle(
                bounds=[[miny, minx], [maxy, maxx]],
                color="blue",
                fill=True,
                fill_color="blue",
                fill_opacity=0.3,
                popup="Flood Inundation Zone"
            ).add_to(m)
        elif sc_type == "earthquake":
            folium.Circle(
                location=[ey, ex],
                radius=radius * 111000, # Approx meters
                color="red",
                fill=True,
                fill_color="red",
                fill_opacity=0.3,
                popup="Earthquake Radial Damage Zone"
            ).add_to(m)

        st_folium(m, width="100%", height=500)
