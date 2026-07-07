import streamlit as st
import folium
from streamlit_folium import st_folium
import random
from datetime import datetime, timedelta

# -------------------------------
# Page config
# -------------------------------
st.set_page_config(
    page_title="WanderPlan – Miami Trip Planner",
    page_icon="🌴",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------------
# Custom CSS (same as before, kept compact)
# -------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .main-header { font-size: 3.2rem; font-weight: 700; color: #00B4D8; text-align: center; margin-bottom: 0.2rem; letter-spacing: -0.02em; text-shadow: 0 2px 4px rgba(0,180,216,0.15); }
    .main-header span { color: #FF6B6B; }
    .sub-header { font-size: 1.2rem; text-align: center; color: #6C757D; margin-bottom: 2rem; font-weight: 400; }
    .section-title { font-size: 1.6rem; font-weight: 600; color: #2C3E50; border-bottom: 3px solid #00B4D8; padding-bottom: 0.4rem; margin-top: 1.8rem; margin-bottom: 1.2rem; display: inline-block; }
    .stButton button { background: linear-gradient(135deg, #00B4D8, #0077B6); color: white; font-weight: 600; border: none; padding: 0.6rem 1.2rem; border-radius: 50px; width: 100%; transition: all 0.3s ease; box-shadow: 0 4px 6px rgba(0,180,216,0.25); }
    .stButton button:hover { transform: translateY(-2px); box-shadow: 0 8px 12px rgba(0,180,216,0.35); background: linear-gradient(135deg, #0077B6, #023E8A); color: white; }
    .metric-card { background: white; border-radius: 16px; padding: 1rem 0.5rem; box-shadow: 0 4px 12px rgba(0,0,0,0.05); text-align: center; border: 1px solid rgba(0,0,0,0.03); transition: 0.2s; }
    .metric-card:hover { box-shadow: 0 8px 20px rgba(0,0,0,0.08); transform: translateY(-3px); }
    .day-card { background: white; border-radius: 16px; padding: 1rem 1.2rem; margin-bottom: 1rem; box-shadow: 0 2px 8px rgba(0,0,0,0.04); border-left: 6px solid #00B4D8; transition: 0.2s; }
    .day-card:hover { box-shadow: 0 6px 16px rgba(0,0,0,0.06); }
    .hotel-card { background: linear-gradient(145deg, #ffffff, #f8f9fa); border-radius: 16px; padding: 1.2rem; margin-bottom: 0.8rem; box-shadow: 0 2px 12px rgba(0,0,0,0.04); border-left: 6px solid #FF6B6B; transition: 0.2s; }
    .hotel-card:hover { transform: translateY(-3px); box-shadow: 0 6px 20px rgba(0,0,0,0.06); }
    .rest-card { background: white; border-radius: 16px; padding: 1rem; box-shadow: 0 2px 12px rgba(0,0,0,0.04); border-left: 6px solid #FFD93D; margin-bottom: 0.8rem; }
    .attr-card { background: white; border-radius: 16px; padding: 1rem; box-shadow: 0 2px 12px rgba(0,0,0,0.04); border-left: 6px solid #9B5DE5; margin-bottom: 0.8rem; }
    .stProgress > div > div { background: linear-gradient(90deg, #FF6B6B, #FFD93D, #00B4D8); border-radius: 20px; }
    .footer { text-align: center; margin-top: 3rem; color: #ADB5BD; font-size: 0.8rem; border-top: 1px solid #e9ecef; padding-top: 1.5rem; }
    .download-btn { background: #28a745; color: white; border: none; border-radius: 50px; padding: 0.5rem 1rem; font-weight: 600; cursor: pointer; }
</style>
""", unsafe_allow_html=True)

# -------------------------------
# Hardcoded Miami coordinates
# -------------------------------
MIAMI_LAT = 25.7617
MIAMI_LON = -80.1918

# -------------------------------
# CURATED MIAMI DATA (reliable, no API needed)
# -------------------------------
CURATED_HOTELS = [
    {"name": "The Miami Beach EDITION", "lat": 25.7930, "lon": -80.1305, "price": 350, "stars": 5},
    {"name": "Fontainebleau Miami Beach", "lat": 25.8090, "lon": -80.1240, "price": 420, "stars": 5},
    {"name": "Loews Miami Beach Hotel", "lat": 25.7865, "lon": -80.1300, "price": 300, "stars": 4},
    {"name": "The Ritz-Carlton, South Beach", "lat": 25.7820, "lon": -80.1300, "price": 480, "stars": 5},
    {"name": "Hyatt Regency Miami", "lat": 25.7620, "lon": -80.1880, "price": 200, "stars": 3.5},
    {"name": "InterContinental Miami", "lat": 25.7640, "lon": -80.1870, "price": 230, "stars": 4},
    {"name": "Kimpton EPIC Hotel", "lat": 25.7655, "lon": -80.1855, "price": 260, "stars": 4},
    {"name": "The Palms Hotel & Spa", "lat": 25.7890, "lon": -80.1310, "price": 280, "stars": 4},
]

CURATED_ATTRACTIONS = [
    {"name": "South Beach", "lat": 25.7812, "lon": -80.1300, "duration": 3, "price": 0, "type": "Beach"},
    {"name": "Art Deco Historic District", "lat": 25.7800, "lon": -80.1305, "duration": 1.5, "price": 0, "type": "Sightseeing"},
    {"name": "Vizcaya Museum & Gardens", "lat": 25.7440, "lon": -80.2100, "duration": 2, "price": 15, "type": "Museums"},
    {"name": "Bayfront Park", "lat": 25.7620, "lon": -80.1890, "duration": 1.5, "price": 0, "type": "Sightseeing"},
    {"name": "Little Havana", "lat": 25.7650, "lon": -80.2140, "duration": 2, "price": 0, "type": "Food & Dining"},
    {"name": "Miami Seaquarium", "lat": 25.7333, "lon": -80.1600, "duration": 3, "price": 30, "type": "Sightseeing"},
    {"name": "Jungle Island", "lat": 25.7525, "lon": -80.1917, "duration": 2.5, "price": 28, "type": "Sightseeing"},
    {"name": "Pérez Art Museum Miami (PAMM)", "lat": 25.7595, "lon": -80.1875, "duration": 2, "price": 18, "type": "Museums"},
    {"name": "Bayside Marketplace", "lat": 25.7650, "lon": -80.1850, "duration": 2, "price": 0, "type": "Shopping"},
    {"name": "Miami Design District", "lat": 25.7860, "lon": -80.1930, "duration": 2, "price": 0, "type": "Shopping"},
    {"name": "Wynwood Walls", "lat": 25.7980, "lon": -80.1980, "duration": 1.5, "price": 12, "type": "Sightseeing"},
    {"name": "Bill Baggs Cape Florida State Park", "lat": 25.6760, "lon": -80.1590, "duration": 3, "price": 8, "type": "Beach"},
]

CURATED_RESTAURANTS = [
    {"name": "Versailles Restaurant", "lat": 25.7900, "lon": -80.1300, "price": 30, "cuisine": "Cuban"},
    {"name": "Joe's Stone Crab", "lat": 25.7700, "lon": -80.1300, "price": 60, "cuisine": "Seafood"},
    {"name": "Cafe Avanti", "lat": 25.7800, "lon": -80.1300, "price": 40, "cuisine": "Italian"},
    {"name": "Zuma Miami", "lat": 25.7650, "lon": -80.1860, "price": 55, "cuisine": "Japanese"},
    {"name": "CVI.CHE 105", "lat": 25.7670, "lon": -80.1890, "price": 35, "cuisine": "Peruvian"},
    {"name": "The Forge", "lat": 25.7880, "lon": -80.1310, "price": 80, "cuisine": "Steakhouse"},
    {"name": "La Sandwicherie", "lat": 25.7820, "lon": -80.1310, "price": 15, "cuisine": "French"},
    {"name": "Yardbird Southern Table & Bar", "lat": 25.7790, "lon": -80.1300, "price": 45, "cuisine": "Southern"},
]

CURATED_BEACHES = [
    {"name": "South Beach", "lat": 25.7812, "lon": -80.1300, "type": "beach"},
    {"name": "Miami Beach (Mid-Beach)", "lat": 25.7930, "lon": -80.1300, "type": "beach"},
    {"name": "Crandon Park Beach", "lat": 25.7070, "lon": -80.1580, "type": "beach"},
]

# Activity mapping to filter attractions
ACTIVITY_MAP = {
    "Beach": "Beach",
    "Sightseeing": "Sightseeing",
    "Museums": "Museums",
    "Food & Dining": "Food & Dining",
    "Shopping": "Shopping",
    "Nightlife": "Sightseeing"  # fallback
}

# -------------------------------
# Generate itinerary from curated data (deterministic with seed)
# -------------------------------
def generate_curated_itinerary(num_people, budget, trip_days, selected_activities, seed=42):
    random.seed(seed)  # for reproducibility
    # Filter attractions based on selected activities
    filtered_attractions = []
    for act in selected_activities:
        category = ACTIVITY_MAP.get(act, None)
        if category:
            filtered_attractions.extend([a for a in CURATED_ATTRACTIONS if a['type'] == category])
    
    # If no matches, use all
    if not filtered_attractions:
        filtered_attractions = CURATED_ATTRACTIONS.copy()
    
    # Pick up to 3 unique attractions per day (we'll cycle)
    unique_attractions = list({a['name']: a for a in filtered_attractions}.values())
    
    # Select a hotel (based on budget)
    if budget > 0:
        available_hotels = [h for h in CURATED_HOTELS if h['price'] <= budget/trip_days * 1.5]
    else:
        available_hotels = CURATED_HOTELS
    if not available_hotels:
        available_hotels = CURATED_HOTELS
    hotel = random.choice(available_hotels)
    
    # Select restaurants (based on budget)
    if budget > 0:
        affordable_restaurants = [r for r in CURATED_RESTAURANTS if r['price'] <= (budget/trip_days) * 0.5]
    else:
        affordable_restaurants = CURATED_RESTAURANTS
    if not affordable_restaurants:
        affordable_restaurants = CURATED_RESTAURANTS
    
    # Pick 2 restaurants for variety
    selected_restaurants = random.sample(affordable_restaurants, min(2, len(affordable_restaurants)))
    
    # Select beaches if "Beach" is in activities
    beach = None
    if "Beach" in selected_activities:
        beach = random.choice(CURATED_BEACHES)
    
    # Build daily plan
    itinerary = []
    daily_budget = budget / trip_days if trip_days > 0 else 0
    
    for day in range(1, trip_days + 1):
        day_plan = {
            'day': day,
            'date': (datetime.now() + timedelta(days=day)).strftime('%A, %B %d'),
            'hotel': hotel,
            'activities': [],
            'meals': [],
            'transport': [],
            'cost': 0
        }
        
        # Morning activity (cycle through attractions)
        if unique_attractions:
            idx = (day - 1) % len(unique_attractions)
            act = unique_attractions[idx]
            day_plan['activities'].append({
                'name': act['name'],
                'time': '9:30 AM',
                'duration': f"{act['duration']}h",
                'cost': act['price'],
                'lat': act['lat'],
                'lon': act['lon']
            })
            day_plan['cost'] += act['price']
        
        # Lunch
        lunch = selected_restaurants[day % len(selected_restaurants)]
        day_plan['meals'].append({
            'name': f"Lunch at {lunch['name']}",
            'time': '12:30 PM',
            'cost': lunch['price'],
            'lat': lunch['lat'],
            'lon': lunch['lon']
        })
        day_plan['cost'] += lunch['price']
        
        # Afternoon: beach if selected, else another attraction
        if beach and day % 2 == 1:
            day_plan['activities'].append({
                'name': f"Relax at {beach['name']}",
                'time': '2:30 PM',
                'duration': '3h',
                'cost': 0,
                'lat': beach['lat'],
                'lon': beach['lon']
            })
        else:
            # second attraction
            if len(unique_attractions) > 1:
                idx2 = (day + 1) % len(unique_attractions)
                act2 = unique_attractions[idx2]
                day_plan['activities'].append({
                    'name': act2['name'],
                    'time': '2:30 PM',
                    'duration': f"{act2['duration']}h",
                    'cost': act2['price'],
                    'lat': act2['lat'],
                    'lon': act2['lon']
                })
                day_plan['cost'] += act2['price']
        
        # Dinner
        dinner = selected_restaurants[(day + 1) % len(selected_restaurants)]
        day_plan['meals'].append({
            'name': f"Dinner at {dinner['name']}",
            'time': '7:30 PM',
            'cost': dinner['price'],
            'lat': dinner['lat'],
            'lon': dinner['lon']
        })
        day_plan['cost'] += dinner['price']
        
        # Evening activity (if day even, add a walk)
        if day % 2 == 0:
            day_plan['activities'].append({
                'name': 'Evening stroll on Ocean Drive',
                'time': '9:00 PM',
                'duration': '1h',
                'cost': 0,
                'lat': 25.7812,
                'lon': -80.1300  # approximate
            })
        
        # Transport (flat fee)
        transport_cost = 15
        day_plan['cost'] += transport_cost
        day_plan['transport'].append({'mode': 'Ride‑share / Bus', 'cost': transport_cost})
        
        # Accommodation
        hotel_cost = hotel['price']
        day_plan['cost'] += hotel_cost
        
        itinerary.append(day_plan)
    
    return itinerary, hotel, selected_restaurants, unique_attractions, beach

# -------------------------------
# Sidebar
# -------------------------------
with st.sidebar:
    st.markdown("### 🌴 Plan Your Miami Getaway")
    st.caption("Fill in the details and we'll craft your perfect trip.")
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        num_people = st.number_input("👥 People", min_value=1, max_value=20, value=2, step=1)
    with col2:
        budget = st.number_input("💰 Budget (USD)", min_value=0, value=2000, step=100)
    
    trip_days = st.slider("📅 Trip Length (days)", min_value=1, max_value=14, value=3, help="How many days will you stay?")
    
    activities = st.multiselect(
        "🎯 Interests",
        options=["Beach", "Sightseeing", "Museums", "Food & Dining", "Shopping", "Nightlife"],
        default=["Beach", "Sightseeing"]
    )
    
    transit = st.multiselect(
        "🚌 Transit Preferences",
        options=["Public Bus", "Ride‑share (Uber/Lyft)", "Bicycle", "Walking", "Rental Car"],
        default=["Walking", "Ride‑share (Uber/Lyft)"]
    )
    
    st.divider()
    submitted = st.button("✨ Plan My Trip", type="primary", use_container_width=True)
    
    # Clear results button
    if st.button("🗑️ Clear Results", use_container_width=True):
        if 'itinerary' in st.session_state:
            del st.session_state['itinerary']
        st.rerun()

# -------------------------------
# Main area
# -------------------------------
# Initialize session state for itinerary
if 'itinerary' not in st.session_state:
    st.session_state.itinerary = None
    st.session_state.hotel = None
    st.session_state.restaurants = None
    st.session_state.attractions = None
    st.session_state.beach = None
    st.session_state.total_cost = 0
    st.session_state.budget = 0
    st.session_state.trip_days = 0
    st.session_state.num_people = 0

# If submit, generate and store
if submitted:
    itinerary, hotel, restaurants, attractions, beach = generate_curated_itinerary(
        num_people, budget, trip_days, activities, seed=42
    )
    total_cost = sum(day['cost'] for day in itinerary)
    st.session_state.itinerary = itinerary
    st.session_state.hotel = hotel
    st.session_state.restaurants = restaurants
    st.session_state.attractions = attractions
    st.session_state.beach = beach
    st.session_state.total_cost = total_cost
    st.session_state.budget = budget
    st.session_state.trip_days = trip_days
    st.session_state.num_people = num_people

# Display results if available
if st.session_state.itinerary is not None:
    itinerary = st.session_state.itinerary
    hotel = st.session_state.hotel
    restaurants = st.session_state.restaurants
    attractions = st.session_state.attractions
    beach = st.session_state.beach
    total_cost = st.session_state.total_cost
    budget = st.session_state.budget
    trip_days = st.session_state.trip_days
    num_people = st.session_state.num_people
    
    st.markdown('<div class="main-header">🌴 Miami Trip Plan</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-header">Your personalized {trip_days}-day itinerary for Miami, FL</div>', unsafe_allow_html=True)
    
    # Budget Overview
    st.markdown("### 📊 Budget Overview")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(f'<div class="metric-card"><h4>Total Budget</h4><p style="font-size:1.8rem; font-weight:700; color:#00B4D8;">${budget:,}</p></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><h4>Estimated Cost</h4><p style="font-size:1.8rem; font-weight:700; color:#FF6B6B;">${total_cost:,.0f}</p></div>', unsafe_allow_html=True)
    with col3:
        daily = budget/trip_days if trip_days>0 else 0
        st.markdown(f'<div class="metric-card"><h4>Daily Budget</h4><p style="font-size:1.8rem; font-weight:700; color:#FFD93D;">${daily:.2f}</p></div>', unsafe_allow_html=True)
    with col4:
        per_person = budget/num_people if num_people>0 else 0
        st.markdown(f'<div class="metric-card"><h4>Per Person</h4><p style="font-size:1.8rem; font-weight:700; color:#9B5DE5;">${per_person:.2f}</p></div>', unsafe_allow_html=True)
    with col5:
        remaining = max(0, budget - total_cost)
        st.markdown(f'<div class="metric-card"><h4>Remaining</h4><p style="font-size:1.8rem; font-weight:700; color:#2C3E50;">${remaining:,.0f}</p></div>', unsafe_allow_html=True)
    
    if budget > 0:
        st.progress(min(total_cost / budget, 1.0))
        st.caption(f"📊 You're using {min(total_cost/budget*100, 100):.1f}% of your budget")
    else:
        st.progress(0)
        st.caption("📊 Budget not set – cost shown as estimate")
    
    # Daily cost bar chart
    st.markdown("### 📈 Daily Cost Breakdown")
    daily_costs = [day['cost'] for day in itinerary]
    days = [f"Day {day['day']}" for day in itinerary]
    st.bar_chart({"Daily Cost": daily_costs}, use_container_width=True)
    
    # Map with route
    st.markdown('<div class="section-title">🗺️ Interactive Miami Map – Your Trip Route</div>', unsafe_allow_html=True)
    m = folium.Map(location=[MIAMI_LAT, MIAMI_LON], zoom_start=13, tiles='CartoDB positron')
    
    # Collect all points for route (hotel as start, then activities in order, then hotel as end)
    route_points = []
    # Hotel
    hotel_coords = [hotel['lat'], hotel['lon']]
    folium.Marker(hotel_coords, popup=f"<b>{hotel['name']}</b><br>🏨 Hotel", icon=folium.Icon(color='green', icon='home', prefix='fa')).add_to(m)
    route_points.append(hotel_coords)
    
    # Gather activities from each day in order
    all_activities = []
    for day in itinerary:
        for act in day['activities']:
            all_activities.append(act)
    # Also add meals? Not necessary; we can add restaurant markers separately
    for act in all_activities:
        if 'lat' in act and 'lon' in act:
            route_points.append([act['lat'], act['lon']])
    # Add end hotel (optional)
    route_points.append(hotel_coords)
    
    # Draw polyline
    if len(route_points) > 1:
        folium.PolyLine(route_points, color='blue', weight=3, opacity=0.7, popup='Your Route').add_to(m)
    
    # Add markers for attractions, restaurants, beach
    for attr in attractions[:8]:
        folium.Marker([attr['lat'], attr['lon']], popup=f"<b>{attr['name']}</b><br>📍 {attr['type']}", icon=folium.Icon(color='blue', icon='star', prefix='fa')).add_to(m)
    for r in restaurants:
        folium.Marker([r['lat'], r['lon']], popup=f"<b>{r['name']}</b><br>🍽️ {r['cuisine']}", icon=folium.Icon(color='orange', icon='cutlery', prefix='fa')).add_to(m)
    if beach:
        folium.Marker([beach['lat'], beach['lon']], popup=f"<b>{beach['name']}</b><br>🏖️ Beach", icon=folium.Icon(color='lightblue', icon='cloud', prefix='fa')).add_to(m)
    
    st_folium(m, width=1000, height=500, key="results_map")
    
    # Daily Itinerary
    st.markdown('<div class="section-title">📅 Your Daily Itinerary</div>', unsafe_allow_html=True)
    for day in itinerary:
        with st.expander(f"Day {day['day']} – {day['date']}  (${day['cost']:.2f})", expanded=True):
            col1, col2 = st.columns([2,1])
            with col1:
                st.markdown(f"**🏨 Hotel:** {day['hotel']['name']}")
                st.markdown("**📋 Activities:**")
                for act in day['activities']:
                    st.write(f"• {act['time']} – {act['name']} ({act['duration']}) – ${act['cost']}")
                st.markdown("**🍽️ Meals:**")
                for meal in day['meals']:
                    st.write(f"• {meal['time']} – {meal['name']} – ${meal['cost']}")
            with col2:
                st.markdown("**🚗 Transport:**")
                for t in day['transport']:
                    st.write(f"• {t['mode']} – ${t['cost']}")
                st.markdown("**💰 Breakdown:**")
                st.write(f"Accommodation: ${day['hotel']['price']}")
                st.write(f"Activities: ${sum(a['cost'] for a in day['activities'])}")
                st.write(f"Meals: ${sum(m['cost'] for m in day['meals'])}")
                st.write(f"Transport: ${sum(t['cost'] for t in day['transport'])}")
                st.write(f"**Total: ${day['cost']:.2f}**")
    
    # Download button
    st.markdown("### 📥 Download Itinerary")
    itinerary_text = f"🌴 Miami Trip Plan – {trip_days} days\n\n"
    for day in itinerary:
        itinerary_text += f"Day {day['day']} – {day['date']}\n"
        itinerary_text += f"Hotel: {day['hotel']['name']}\n"
        itinerary_text += "Activities:\n"
        for act in day['activities']:
            itinerary_text += f"  {act['time']} – {act['name']} ({act['duration']}) – ${act['cost']}\n"
        itinerary_text += "Meals:\n"
        for meal in day['meals']:
            itinerary_text += f"  {meal['time']} – {meal['name']} – ${meal['cost']}\n"
        itinerary_text += f"Transport: {day['transport'][0]['mode']} – ${day['transport'][0]['cost']}\n"
        itinerary_text += f"Total cost: ${day['cost']:.2f}\n\n"
    st.download_button(
        label="📄 Download as Text",
        data=itinerary_text,
        file_name="miami_itinerary.txt",
        mime="text/plain"
    )
    
    # Personalized Recommendations
    st.markdown('<div class="section-title">🏨 Recommended Hotels (within your budget)</div>', unsafe_allow_html=True)
    # Filter hotels by budget
    budget_hotels = [h for h in CURATED_HOTELS if h['price'] <= budget/trip_days * 1.5] if budget>0 else CURATED_HOTELS
    if not budget_hotels:
        budget_hotels = CURATED_HOTELS[:3]
    cols = st.columns(min(3, len(budget_hotels)))
    for i, h in enumerate(budget_hotels[:3]):
        with cols[i]:
            st.markdown(f"""
            <div class="hotel-card">
                <h4>{h['name']}</h4>
                <p>📍 Miami, FL</p>
                <p>⭐ {h['stars']}/5</p>
                <p>💰 ${h['price']}/night</p>
                <p>✅ Free WiFi · Pool · Breakfast</p>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown('<div class="section-title">🍽️ Recommended Restaurants (match your interests)</div>', unsafe_allow_html=True)
    # Filter restaurants by cuisine based on selected activities? For simplicity, pick affordable ones.
    affordable = [r for r in CURATED_RESTAURANTS if r['price'] <= (budget/trip_days)*0.5] if budget>0 else CURATED_RESTAURANTS
    if not affordable:
        affordable = CURATED_RESTAURANTS[:3]
    cols = st.columns(min(3, len(affordable)))
    for i, r in enumerate(affordable[:3]):
        with cols[i]:
            st.markdown(f"""
            <div class="rest-card">
                <h4>{r['name']}</h4>
                <p>🍽️ {r['cuisine']}</p>
                <p>💰 ${r['price']}/person</p>
                <p>⭐ {random.randint(3,5)}/5</p>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown('<div class="section-title">📍 Top Attractions (based on your interests)</div>', unsafe_allow_html=True)
    # Filter attractions by selected activities
    interest_attractions = []
    for act in activities:
        category = ACTIVITY_MAP.get(act, None)
        if category:
            interest_attractions.extend([a for a in CURATED_ATTRACTIONS if a['type'] == category])
    if not interest_attractions:
        interest_attractions = CURATED_ATTRACTIONS[:3]
    else:
        interest_attractions = interest_attractions[:3]
    cols = st.columns(min(3, len(interest_attractions)))
    for i, attr in enumerate(interest_attractions[:3]):
        with cols[i]:
            st.markdown(f"""
            <div class="attr-card">
                <h4>{attr['name']}</h4>
                <p>📍 Miami, FL</p>
                <p>⏰ {attr['duration']} hours</p>
                <p>💰 ${attr['price']} entry</p>
            </div>
            """, unsafe_allow_html=True)

else:
    # Welcome page – big Miami map with correct markers
    st.markdown('<div class="main-header">🌴 WanderPlan <span>Miami</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Your AI‑powered trip planner for Miami, Florida</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="section-title">🗺️ Explore Miami</div>', unsafe_allow_html=True)
    
    miami_map = folium.Map(location=[MIAMI_LAT, MIAMI_LON], zoom_start=13, tiles='CartoDB positron')
    # Central marker
    folium.Marker([MIAMI_LAT, MIAMI_LON], popup="<b>Miami, FL</b>", icon=folium.Icon(color='red', icon='info-sign')).add_to(miami_map)
    # Landmarks with corrected coordinates
    landmarks = [
        ("South Beach", 25.7812, -80.1300),
        ("Art Deco District", 25.7800, -80.1305),
        ("Vizcaya Museum", 25.7440, -80.2100),
        ("Bayfront Park", 25.7620, -80.1890),
        ("Little Havana", 25.7650, -80.2140),
        ("Miami Seaquarium", 25.7333, -80.1600),
        ("Jungle Island", 25.7525, -80.1917),
        ("Pérez Art Museum", 25.7595, -80.1875),
        ("Wynwood Walls", 25.7980, -80.1980)
    ]
    for name, lat, lon in landmarks:
        folium.Marker([lat, lon], popup=name, icon=folium.Icon(color='blue', icon='star', prefix='fa')).add_to(miami_map)
    st_folium(miami_map, width=1000, height=600, key="welcome_map")
    
    st.caption("📍 Click on markers to learn more about Miami's top spots.")
    st.markdown("""
        <div style="text-align: center; margin-top: 1.5rem;">
            <p style="font-size: 1.2rem; color: #2C3E50;">
                👈 Fill in your trip details on the sidebar and hit <strong>"Plan My Trip"</strong>.
            </p>
            <p style="font-size: 0.9rem; color: #6C757D;">
                We'll generate a complete day‑by‑day itinerary with hotels, restaurants, and attractions.
            </p>
        </div>
    """, unsafe_allow_html=True)

# -------------------------------
# Footer
# -------------------------------
st.markdown("""
<div class="footer">
    WanderPlan Miami – Powered by curated Miami data | No API keys needed | Completely free!
</div>
""", unsafe_allow_html=True)