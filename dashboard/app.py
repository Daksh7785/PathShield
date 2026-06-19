"""
Route Resilience — Main Streamlit Application
"""
import streamlit as st

st.set_page_config(
    page_title="Route Resilience | ISRO",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for dark-themed, modern metrics layouts
st.markdown("""
<style>
.metric-card {
    background: #1e2530;
    border-radius: 8px;
    padding: 16px;
    border-left: 4px solid #00d4aa;
    margin: 8px 0;
}
.critical-badge { color: #ff4444; font-weight: bold; }
.safe-badge { color: #00d4aa; font-weight: bold; }
.stButton>button {
    background-color: #00d4aa;
    color: #0a0f1a;
    border: none;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# Navigation
st.sidebar.title("🛰️ Route Resilience")
st.sidebar.caption("ISRO Urban Intelligence Platform")
st.sidebar.divider()

page = st.sidebar.radio(
    "Navigation",
    ["🏙️ City Overview", "🔴 Bottleneck Analysis", "⚡ Stress Test", "🌊 Disaster Scenario"],
)

if page == "🏙️ City Overview":
    from dashboard.pages.city_overview import render
    render()
elif page == "🔴 Bottleneck Analysis":
    from dashboard.pages.bottleneck_analysis import render
    render()
elif page == "⚡ Stress Test":
    from dashboard.pages.stress_test import render
    render()
elif page == "🌊 Disaster Scenario":
    from dashboard.pages.disaster_scenario import render
    render()
