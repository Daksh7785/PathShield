# RouteGuard AI — User & Platform Operator Guide

This document describes how to operate the RouteGuard AI Web Workbench.

## Exploring the GIS Workbench

1. **City Selection**: Select a city (e.g. Bengaluru, Delhi, Mumbai, New York, Tokyo) from the dropdown in the header to focus the map canvas.
2. **Global Geocoding Search**: Enter any location in the search bar (e.g. "Tokyo") and click **Go** to re-center the viewport.
3. **Criticality Overlays**: Toggle the **Centrality** or **Confidence** layers in the sidebar to highlight articulation points and vulnerable road networks.
4. **Traffic Advisories**: View localized closures and lane narrowings in the sidebar incidents panel.

---

## Running Route Computations

1. Click on a node marker on the map to set the **Source Node**.
2. Click on a second node marker on the map to set the **Target Node**.
3. Click **Calculate Routes** in the sidebar.
4. The workbench will draw:
   - **Blue Solid Polyline**: The shortest path, optimized for current traffic congestion and avoiding closed routes.
   - **Green Dashed Polyline**: The alternative/detour route.

---

## Consulting the AI Copilot

1. Click on the message bubble in the bottom right corner to open the AI Copilot.
2. Type queries like:
   - *What happens if a bridge fails?* (Simulates a network node ablation)
   - *Show critical corridors in Bengaluru* (Runs centrality analysis)
   - *Calculate safe evacuation routes* (Draws a route bypassing active flood zones)
