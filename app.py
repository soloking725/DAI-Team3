import streamlit as st
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

# -------------------------------
# Page config
# -------------------------------
st.set_page_config(
    page_title="Travel Planner",
    page_icon="✈️",
    layout="wide"
)

# -------------------------------
# Custom CSS for a polished look
# -------------------------------
st.markdown("""
    <style>
        .main-header {
            font-size: 3rem;
            font-weight: 700;
            color: #2c3e50;
            text-align: center;
            margin-bottom: 0.5rem;
        }
        .sub-header {
            font-size: 1.2rem;
            text-align: center;
            color: #7f8c8d;
            margin-bottom: 2rem;
        }
        .section-title {
            font-size: 1.5rem;
            font-weight: 600;
            color: #34495e;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 0.3rem;
            margin-top: 1.5rem;
            margin-bottom: 1rem;
        }
        .stButton button {
            background-color: #3498db;
            color: white;
            font-weight: 600;
            width: 100%;
        }
        .stButton button:hover {
            background-color: #2980b9;
            color: white;
        }
        .summary-box {
            background-color: #f8f9fa;
            padding: 1.5rem;
            border-radius: 10px;
            margin-top: 1.5rem;
        }
    </style>
""", unsafe_allow_html=True)

# -------------------------------
# Header
# -------------------------------
st.markdown('<div class="main-header">🌍 WanderPlan</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Your AI‑powered travel companion – start planning your next adventure</div>', unsafe_allow_html=True)

# -------------------------------
# Sidebar – step‑by‑step inputs
# -------------------------------
with st.sidebar:
    st.image("https://www.gstatic.com/travel-frontend/images/hero/flights.jpg", use_container_width=True)  # decorative placeholder
    st.markdown("### ✏️ Tell us about your trip")

    # 1. Destination
    destination = st.text_input("📍 Where do you want to go?", placeholder="e.g., Paris, Tokyo, New York")

    # 2. Group size & budget
    col1, col2 = st.columns(2)
    with col1:
        num_people = st.number_input("👥 Number of people", min_value=1, max_value=20, value=2, step=1)
    with col2:
        budget = st.number_input("💰 Total budget (USD)", min_value=0, value=2000, step=100)

    # 3. Trip length
    trip_days = st.slider("📅 Length of trip (days)", min_value=1, max_value=30, value=7)

    # 4. Activities (multi‑select)
    activities = st.multiselect(
        "🎯 What are you interested in?",
        options=["Food & Dining", "Sightseeing", "Hiking & Nature", "Sports & Adventure", "Museums & Culture", "Beach"],
        default=["Sightseeing", "Food & Dining"]
    )

    # 5. Transit options
    transit = st.multiselect(
        "🚌 Which transit options do you prefer?",
        options=["Public Bus", "Subway/Metro", "Ride‑share (Uber/Lyft)", "Bicycle", "Walking", "Rental Car"],
        default=["Public Bus", "Walking"]
    )

    # Submit button
    submitted = st.button("✨ Plan my trip", type="primary")

# -------------------------------
# Main area – results / map placeholder
# -------------------------------
if submitted:
    if not destination:
        st.warning("Please enter a destination to continue.")
    else:
        st.markdown(f'<div class="section-title">📋 Your trip summary</div>', unsafe_allow_html=True)

        # Display inputs in a nice layout
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Destination", destination)
        col2.metric("Travelers", num_people)
        col3.metric("Budget", f"${budget:,}")
        col4.metric("Duration", f"{trip_days} days")

        st.markdown(f"**Activities:** {', '.join(activities) if activities else 'Not selected'}")
        st.markdown(f"**Preferred transit:** {', '.join(transit) if transit else 'Not selected'}")

        # -------------------------------
        # Placeholder for Google Maps / map
        # -------------------------------
        st.markdown('<div class="section-title">🗺️ Suggested area (map placeholder)</div>', unsafe_allow_html=True)

        # Generate some dummy points around a random city (if destination is entered)
        # In a real app, you'd use geocoding + Google Maps API
        # Here we just simulate a few random points for visual effect
        if destination:
            # Seed random for reproducibility based on destination name
            random.seed(hash(destination) % 2**32)
            lats = [random.uniform(40.7, 40.8) for _ in range(10)]
            lons = [random.uniform(-74.0, -73.9) for _ in range(10)]
            df = pd.DataFrame({
                'lat': lats,
                'lon': lons
            })
            st.map(df, zoom=12, use_container_width=True)

            st.caption("📌 *This is a placeholder map. In production, we'll integrate Google Maps to show actual destinations, points of interest, and transit routes.*")
        else:
            st.info("Enter a destination above to see a map preview.")

        # Additional info – maybe some cost breakdown (just for demo)
        st.markdown('<div class="section-title">💡 Quick estimate</div>', unsafe_allow_html=True)
        avg_daily_cost = budget / trip_days if trip_days > 0 else 0
        st.metric("Average daily budget per person", f"${avg_daily_cost / num_people:.2f}" if num_people > 0 else "N/A")
        st.progress(min(avg_daily_cost / 500, 1.0))  # just a visual bar

        # Suggest activities based on selection (demo)
        if activities:
            st.markdown("#### 🧭 Suggested activities based on your interests:")
            for act in activities:
                st.write(f"- **{act}**: we'll find top-rated spots and tours in {destination} (coming soon!)")
        else:
            st.write("Select some activities to get personalized suggestions.")

else:
    # Before submission: show a friendly welcome message
    st.markdown("""
        <div style="text-align: center; margin-top: 2rem;">
            <p style="font-size: 1.1rem; color: #555;">
                 Fill in your trip details on the sidebar, then click <strong>"Plan my trip"</strong>.
            </p>
            <p style="font-size: 0.9rem; color: #888;">
                We'll help you choose the best destinations, activities, and transit options.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Placeholder map with generic points
    st.markdown('<div class="section-title">🗺️ Explore the world</div>', unsafe_allow_html=True)
    df_world = pd.DataFrame({
        'lat': [40.7128, 34.0522, 51.5074, -33.8688, 35.6895, 48.8566],
        'lon': [-74.0060, -118.2437, -0.1278, 151.2093, 139.6917, 2.3522]
    })
    st.map(df_world, zoom=1, use_container_width=True)
    st.caption("📍 Some popular destinations – enter yours above to zoom in.")

# -------------------------------
# Footer
# -------------------------------
st.markdown("---")
st.caption("WanderPlan v0.1 – built with ❤️ using Streamlit. Google Maps integration coming soon.")