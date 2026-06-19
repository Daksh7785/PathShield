"""Bottleneck analysis page displaying top intersections and centrality stats."""
import streamlit as st
import requests
import plotly.graph_objects as go
import yaml

API_BASE = "http://localhost:8000/api/v1"

def get_vulnerability_report(city_id: str) -> list:
    try:
        r = requests.get(f"{API_BASE}/analysis/{city_id}/vulnerability-report", timeout=10)
        return r.json() if r.status_code == 200 else []
    except:
        return []

def render():
    st.title("🔴 Bottleneck Analysis (Gatekeeper Nodes)")
    
    with open("configs/cities.yaml") as f:
        cities_config = yaml.safe_load(f)
        
    city_key = st.selectbox(
        "Select City",
        options=list(cities_config["cities"].keys()),
        format_func=lambda k: cities_config["cities"][k]["name"]
    )
    
    with st.spinner("Analyzing network centralities..."):
        report = get_vulnerability_report(city_key)
        
    if not report:
        st.warning("No data found. Ensure the demo setup script or inference runs have completed successfully.")
        return
        
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Top Critical Intersections")
        
        # Display as a table
        table_data = []
        for i, item in enumerate(report[:15]):
            table_data.append({
                "Rank": i + 1,
                "Node ID": item.get("removed_node_id", "N/A"),
                "Betweenness": item.get("betweenness", 0.0),
                "LCC Loss %": item.get("lcc_loss_percent", 0.0),
                "Detour Factor": item.get("path_increase_factor", 1.0),
                "Status": "🔴 Critical" if item.get("critical") else "🟢 Normal"
            })
        st.dataframe(table_data, use_container_width=True)
        
    with col2:
        st.subheader("Centrality Distribution")
        
        # Plot centrality scores
        node_ids = [str(x.get("removed_node_id")) for x in report[:15]]
        scores = [x.get("betweenness", 0.0) for x in report[:15]]
        
        fig = go.Figure(data=[
            go.Bar(
                x=node_ids,
                y=scores,
                marker_color='#ff3333'
            )
        ])
        
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            xaxis_title="Node ID",
            yaxis_title="Betweenness Centrality",
            margin=dict(l=20, r=20, t=20, b=20),
            height=350
        )
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Planning Recommendations")
    st.info(
        "Intersections with high Betweenness Centrality act as single-points-of-failure. "
        "Planners should target these locations for redundancy improvements, such as establishing "
        "alternative transit connectors or widening key arterial routes."
    )
