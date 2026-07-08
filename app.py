import streamlit as st
import folium
from streamlit_folium import st_folium
import random
import math
from datetime import datetime, timedelta

# TODO(AI): Future - replace generate_curated_itinerary() with an LLM call.
# The curated data below becomes "grounding context" for the LLM. The same
# input/output contract lets us swap planners without touching the UI layer.

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
# Haversine distance (km)
# -------------------------------
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

# -------------------------------
# Input validation
# -------------------------------
def validate_inputs(num_people, budget, trip_days):
    errors = []
    warnings = []
    
    per_day_budget = (budget / num_people / trip_days) if (num_people > 0 and trip_days > 0) else 0
    
    if budget == 0:
        warnings.append("⚠️ No budget set — showing free/low-cost options only.")
    elif per_day_budget < 30:
        errors.append("❌ Budget too low — Miami needs at least $30/person/day. Please increase your budget.")
    elif per_day_budget < 100:
        warnings.append("⚠️ Very tight budget — we'll focus on free attractions and budget meals.")
    
    if num_people > 20:
        errors.append("❌ We can't plan for groups this large yet (max 20). Please contact us for group tours.")
    elif num_people > 10:
        warnings.append("⚠️ Large group — hotel costs assume shared rooms (2 per room). Actual cost may be higher.")
    
    if trip_days > 14:
        warnings.append("⚠️ Very long trip — itinerary may repeat activities.")
    
    return errors, warnings

# -------------------------------
# Transport cost (scales with group)
# -------------------------------
def compute_transit_cost(transit_mode, num_people):
    base = TRANSIT_COST.get(transit_mode, 15)
    if transit_mode in ("Walking", "Bicycle", "Public Bus"):
        return base  # already per-person
    if num_people <= 4:
        return base
    # Split shared transport across group (min 4-person split)
    return max(base / num_people, base / 4)

# Miami center coordinates
MIAMI_LAT = 25.7617
MIAMI_LON = -80.1918

# -------------------------------
# CURATED MIAMI DATA (reliable, no API needed)
# -------------------------------
CURATED_HOTELS = [
    {"name": "The Miami Beach EDITION", "lat": 25.7930, "lon": -80.1305, "price": 350, "stars": 5, "neighborhood": "South Beach"},
    {"name": "Fontainebleau Miami Beach", "lat": 25.8090, "lon": -80.1240, "price": 420, "stars": 5, "neighborhood": "South Beach"},
    {"name": "Loews Miami Beach Hotel", "lat": 25.7865, "lon": -80.1300, "price": 300, "stars": 4, "neighborhood": "South Beach"},
    {"name": "The Ritz-Carlton, South Beach", "lat": 25.7820, "lon": -80.1300, "price": 480, "stars": 5, "neighborhood": "South Beach"},
    {"name": "Hyatt Regency Miami", "lat": 25.7620, "lon": -80.1880, "price": 200, "stars": 3.5, "neighborhood": "Downtown"},
    {"name": "InterContinental Miami", "lat": 25.7640, "lon": -80.1870, "price": 230, "stars": 4, "neighborhood": "Downtown"},
    {"name": "Kimpton EPIC Hotel", "lat": 25.7655, "lon": -80.1855, "price": 260, "stars": 4, "neighborhood": "South Beach"},
    {"name": "The Palms Hotel & Spa", "lat": 25.7890, "lon": -80.1310, "price": 280, "stars": 4, "neighborhood": "South Beach"},
]

CURATED_ATTRACTIONS = [
    {"name": "South Beach", "lat": 25.7812, "lon": -80.1300, "duration": 3, "price": 0, "type": "Beach", "neighborhood": "South Beach"},
    {"name": "Art Deco Historic District", "lat": 25.7800, "lon": -80.1305, "duration": 1.5, "price": 0, "type": "Sightseeing", "neighborhood": "South Beach"},
    {"name": "Vizcaya Museum & Gardens", "lat": 25.7440, "lon": -80.2100, "duration": 2, "price": 15, "type": "Museums", "neighborhood": "Coconut Grove"},
    {"name": "Bayfront Park", "lat": 25.7620, "lon": -80.1890, "duration": 1.5, "price": 0, "type": "Sightseeing", "neighborhood": "Downtown"},
    {"name": "Little Havana", "lat": 25.7650, "lon": -80.2140, "duration": 2, "price": 0, "type": "Food & Dining", "neighborhood": "Little Havana"},
    {"name": "Miami Seaquarium", "lat": 25.7333, "lon": -80.1600, "duration": 3, "price": 30, "type": "Sightseeing", "neighborhood": "Key Biscayne"},
    {"name": "Jungle Island", "lat": 25.7525, "lon": -80.1917, "duration": 2.5, "price": 28, "type": "Sightseeing", "neighborhood": "Downtown"},
    {"name": "Pérez Art Museum Miami (PAMM)", "lat": 25.7595, "lon": -80.1875, "duration": 2, "price": 18, "type": "Museums", "neighborhood": "Downtown"},
    {"name": "Bayside Marketplace", "lat": 25.7650, "lon": -80.1850, "duration": 2, "price": 0, "type": "Shopping", "neighborhood": "Downtown"},
    {"name": "Miami Design District", "lat": 25.7860, "lon": -80.1930, "duration": 2, "price": 0, "type": "Shopping", "neighborhood": "Design District"},
    {"name": "Wynwood Walls", "lat": 25.7980, "lon": -80.1980, "duration": 1.5, "price": 12, "type": "Sightseeing", "neighborhood": "Wynwood"},
    {"name": "Bill Baggs Cape Florida State Park", "lat": 25.6760, "lon": -80.1590, "duration": 3, "price": 8, "type": "Beach", "neighborhood": "Key Biscayne"},
]

CURATED_RESTAURANTS = [
    {"name": "Versailles Restaurant", "lat": 25.7900, "lon": -80.1300, "price": 30, "cuisine": "Cuban", "rating": 4.5, "neighborhood": "Little Havana"},
    {"name": "Joe's Stone Crab", "lat": 25.7700, "lon": -80.1300, "price": 60, "cuisine": "Seafood", "rating": 4.7, "neighborhood": "South Beach"},
    {"name": "Cafe Avanti", "lat": 25.7800, "lon": -80.1300, "price": 40, "cuisine": "Italian", "rating": 4.2, "neighborhood": "South Beach"},
    {"name": "Zuma Miami", "lat": 25.7650, "lon": -80.1860, "price": 55, "cuisine": "Japanese", "rating": 4.6, "neighborhood": "Downtown"},
    {"name": "CVI.CHE 105", "lat": 25.7670, "lon": -80.1890, "price": 35, "cuisine": "Peruvian", "rating": 4.3, "neighborhood": "Downtown"},
    {"name": "The Forge", "lat": 25.7880, "lon": -80.1310, "price": 80, "cuisine": "Steakhouse", "rating": 4.8, "neighborhood": "South Beach"},
    {"name": "La Sandwicherie", "lat": 25.7820, "lon": -80.1310, "price": 15, "cuisine": "French", "rating": 4.1, "neighborhood": "South Beach"},
    {"name": "Yardbird Southern Table & Bar", "lat": 25.7790, "lon": -80.1300, "price": 45, "cuisine": "Southern", "rating": 4.4, "neighborhood": "South Beach"},
]

CURATED_BEACHES = [
    {"name": "South Beach", "lat": 25.7812, "lon": -80.1300, "type": "beach", "neighborhood": "South Beach"},
    {"name": "Miami Beach (Mid-Beach)", "lat": 25.7930, "lon": -80.1300, "type": "beach", "neighborhood": "South Beach"},
    {"name": "Crandon Park Beach", "lat": 25.7070, "lon": -80.1580, "type": "beach", "neighborhood": "Key Biscayne"},
]

CURATED_EVENING_ACTIVITIES = [
    {"name": "Evening stroll on Ocean Drive", "lat": 25.7812, "lon": -80.1300, "duration": 1, "price": 0, "type": "Nightlife", "neighborhood": "South Beach"},
    {"name": "Sunset at Lummus Park", "lat": 25.7820, "lon": -80.1290, "duration": 1, "price": 0, "type": "Sightseeing", "neighborhood": "South Beach"},
    {"name": "Wynwood nightlife", "lat": 25.8010, "lon": -80.1990, "duration": 2, "price": 0, "type": "Nightlife", "neighborhood": "Wynwood"},
    {"name": "South Pointe Park sunset", "lat": 25.7670, "lon": -80.1330, "duration": 1, "price": 0, "type": "Sightseeing", "neighborhood": "South Beach"},
    {"name": "Lincoln Road Mall evening walk", "lat": 25.7905, "lon": -80.1390, "duration": 1.5, "price": 0, "type": "Shopping", "neighborhood": "South Beach"},
]

# Activity mapping to filter attractions
ACTIVITY_MAP = {
    "Beach": "Beach",
    "Sightseeing": "Sightseeing",
    "Museums": "Museums",
    "Food & Dining": "Food & Dining",
    "Shopping": "Shopping",
    "Nightlife": "Nightlife"
}

# Transit cost mapping
TRANSIT_COST = {
    "Public Bus": 3,
    "Ride‑share (Uber/Lyft)": 15,
    "Bicycle": 0,
    "Walking": 0,
    "Rental Car": 35,
}

# -------------------------------
# PLANNING ENGINE (neighborhood-aware, Plan B, transport scaling)
# -------------------------------
def generate_curated_itinerary(num_people, budget, trip_days, selected_activities, selected_transit, start_date, pace="Moderate", room_preference="Shared", planner_backend="curated"):
    """Generate a curated Miami itinerary.
    
    Args:
        pace: "Relaxed" (2 activities/day), "Moderate" (3/day), "Packed" (5/day)
        room_preference: "Shared" (split hotel) or "Private" (each gets own room)
        planner_backend: "curated" (rule-based) — future: "ai" (LLM)
    """
    # Pace → activities per day
    pace_map = {"Relaxed": 2, "Moderate": 3, "Packed": 5}
    activities_per_day = pace_map.get(pace, 3)
    
    # Resolve transit
    if not selected_transit:
        selected_transit = ["Ride‑share (Uber/Lyft)"]
    primary_transit = selected_transit[0]
    transit_cost_pp = compute_transit_cost(primary_transit, num_people)
    
    # Budget math
    per_person_budget = budget / num_people if num_people > 0 else budget
    per_person_daily = per_person_budget / trip_days if trip_days > 0 else 0
    total_daily_budget = budget / trip_days if trip_days > 0 else 0
    
    # ——— Hotel selection ———
    hotel_budget = total_daily_budget * 0.4  # 40% of daily budget for hotel
    if budget > 0:
        available_hotels = sorted([h for h in CURATED_HOTELS if h['price'] <= hotel_budget], key=lambda x: x['price'])
    else:
        available_hotels = sorted(CURATED_HOTELS, key=lambda x: x['price'])
    if not available_hotels:
        available_hotels = sorted(CURATED_HOTELS, key=lambda x: x['price'])
    hotel = available_hotels[0]  # pick cheapest within budget
    hotel_backup = available_hotels[1] if len(available_hotels) > 1 else available_hotels[0]
    
    # ——— Restaurant selection ———
    meal_budget = per_person_daily * 0.3
    if budget > 0:
        affordable_restaurants = sorted([r for r in CURATED_RESTAURANTS if r['price'] <= meal_budget], key=lambda x: x['price'])
    else:
        affordable_restaurants = sorted(CURATED_RESTAURANTS, key=lambda x: x['price'])
    if not affordable_restaurants:
        affordable_restaurants = sorted(CURATED_RESTAURANTS, key=lambda x: x['price'])
    num_restaurants = min(2, len(affordable_restaurants))
    selected_restaurants = random.sample(affordable_restaurants, num_restaurants)
    restaurant_backups = [r for r in affordable_restaurants if r not in selected_restaurants][:2]
    
    # ——— Beach ———
    beach = None
    if "Beach" in selected_activities:
        beach = random.choice(CURATED_BEACHES)
    
    # ——— Filter + group attractions by neighborhood ———
    filtered = []
    for act in selected_activities:
        category = ACTIVITY_MAP.get(act)
        if category:
            filtered.extend([a for a in CURATED_ATTRACTIONS if a['type'] == category])
    if not filtered:
        filtered = CURATED_ATTRACTIONS.copy()
    unique_attractions = list({a['name']: a for a in filtered}.values())
    
    # Group by neighborhood
    neighborhoods = {}
    for a in unique_attractions:
        nb = a.get('neighborhood', 'Other')
        neighborhoods.setdefault(nb, []).append(a)
    
    # Sort each group by distance from hotel (haversine)
    for nb in neighborhoods:
        neighborhoods[nb].sort(key=lambda x: haversine(hotel['lat'], hotel['lon'], x['lat'], x['lon']))
    
    # Pick day zones (rotate through neighborhoods)
    nb_list = list(neighborhoods.keys())
    
    # ——— Evening activities ———
    has_evening = "Nightlife" in selected_activities or "Sightseeing" in selected_activities
    available_evenings = [e for e in CURATED_EVENING_ACTIVITIES if e['type'] in selected_activities] if has_evening else []
    if not available_evenings:
        available_evenings = CURATED_EVENING_ACTIVITIES.copy()
    
    # ——— Build daily plan ———
    itinerary = []
    attraction_backups = []
    
    for day in range(1, trip_days + 1):
        day_date = start_date + timedelta(days=day - 1)
        day_plan = {
            'day': day,
            'date': day_date.strftime('%A, %B %d'),
            'hotel': hotel,
            'activities': [],
            'meals': [],
            'transport': [],
            'cost_per_person': 0,
        }
        
        # Pick today's neighborhood zone
        zone_idx = (day - 1) % len(nb_list)
        zone_name = nb_list[zone_idx]
        zone_attractions = neighborhoods.get(zone_name, [])
        
        # Fill activities up to activities_per_day
        act_count = 0
        used_idx = 0
        for slot in range(activities_per_day):
            if not zone_attractions:
                break
            # Pick from zone
            act = zone_attractions[used_idx % len(zone_attractions)]
            used_idx += 1
            
            times = ["9:30 AM", "12:00 PM", "2:00 PM", "4:30 PM", "7:00 PM"]
            time_str = times[slot] if slot < len(times) else f"{10 + slot}:00 {'AM' if slot < 6 else 'PM'}"
            
            day_plan['activities'].append({
                'name': act['name'],
                'time': time_str,
                'duration': f"{act['duration']}h",
                'cost': act['price'],
                'lat': act['lat'],
                'lon': act['lon'],
                'neighborhood': act.get('neighborhood', ''),
                'distance_from_hotel': round(haversine(hotel['lat'], hotel['lon'], act['lat'], act['lon']), 1)
            })
            day_plan['cost_per_person'] += act['price']
            act_count += 1
        
        # Plan B: backup activity from a different neighborhood
        other_zones = [n for n in nb_list if n != zone_name]
        backup_act = None
        if other_zones:
            backup_zone = neighborhoods.get(other_zones[0], [])
            if backup_zone:
                backup_act = backup_zone[0]
        attraction_backups.append(backup_act)
        
        # ——— Meals ———
        lunch = selected_restaurants[(day - 1) % len(selected_restaurants)]
        dinner = selected_restaurants[day % len(selected_restaurants)]
        
        day_plan['meals'].append({
            'name': f"Lunch at {lunch['name']}",
            'time': '12:30 PM',
            'cost': lunch['price'],
            'lat': lunch['lat'],
            'lon': lunch['lon'],
        })
        day_plan['cost_per_person'] += lunch['price']
        
        day_plan['meals'].append({
            'name': f"Dinner at {dinner['name']}",
            'time': '7:30 PM',
            'cost': dinner['price'],
            'lat': dinner['lat'],
            'lon': dinner['lon'],
        })
        day_plan['cost_per_person'] += dinner['price']
        
        # ——— Beach (on relaxed/moderate pace, alternate days) ———
        if beach and day % 2 == 1 and act_count < activities_per_day:
            day_plan['activities'].append({
                'name': f"Relax at {beach['name']}",
                'time': '3:00 PM',
                'duration': '3h',
                'cost': 0,
                'lat': beach['lat'],
                'lon': beach['lon'],
                'neighborhood': beach.get('neighborhood', ''),
                'distance_from_hotel': round(haversine(hotel['lat'], hotel['lon'], beach['lat'], beach['lon']), 1)
            })
        
        # ——— Evening activity (alternate days) ———
        if has_evening and day % 2 == 0 and available_evenings:
            ev = available_evenings[(day // 2 - 1) % len(available_evenings)]
            day_plan['activities'].append({
                'name': ev['name'],
                'time': '9:00 PM',
                'duration': f"{ev['duration']}h",
                'cost': ev['price'],
                'lat': ev['lat'],
                'lon': ev['lon'],
                'neighborhood': ev.get('neighborhood', ''),
                'distance_from_hotel': round(haversine(hotel['lat'], hotel['lon'], ev['lat'], ev['lon']), 1)
            })
            day_plan['cost_per_person'] += ev['price']
        
        # ——— Transport ———
        day_plan['cost_per_person'] += transit_cost_pp
        day_plan['transport'].append({'mode': primary_transit, 'cost': transit_cost_pp})
        
        # ——— Hotel (room preference) ———
        if room_preference == "Shared":
            hotel_pp = hotel['price'] / num_people
        else:
            hotel_pp = hotel['price']  # each person gets own room
        day_plan['cost_per_person'] += hotel_pp
        
        # ——— Totals ———
        day_plan['cost'] = day_plan['cost_per_person'] * num_people
        
        itinerary.append(day_plan)
    
    # Build return dict (clean contract for future AI swap)
    return {
        'itinerary': itinerary,
        'hotel': hotel,
        'hotel_backup': hotel_backup,
        'restaurants': selected_restaurants,
        'restaurant_backups': restaurant_backups,
        'attractions': unique_attractions,
        'attraction_backups': attraction_backups,
        'beach': beach,
    }

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
    
    start_date = st.date_input(
        "📆 Trip Start Date",
        value=datetime.now() + timedelta(days=7),
        help="What day does your trip start?"
    )
    
    # New options
    pace = st.selectbox(
        "🏃 Trip Pace",
        options=["Relaxed", "Moderate", "Packed"],
        index=1,
        help="Relaxed = 2 activities/day · Moderate = 3 · Packed = 5"
    )
    room_pref = st.radio(
        "🛏️ Room Preference",
        options=["Shared", "Private"],
        help="Shared = hotel split among group · Private = each person gets their own room"
    )
    
    # Validation preview
    errors, warnings = validate_inputs(num_people, budget, trip_days)
    for err in errors:
        st.error(err)
    for warn in warnings:
        st.warning(warn)
    
    st.divider()
    can_submit = len(errors) == 0
    submitted = st.button("✨ Plan My Trip", type="primary", use_container_width=True, disabled=not can_submit)
    
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
    st.session_state.result = None
    st.session_state.total_cost = 0
    st.session_state.budget = 0
    st.session_state.trip_days = 0
    st.session_state.num_people = 0

# If submit, generate and store
if submitted:
    result = generate_curated_itinerary(
        num_people, budget, trip_days, activities, transit, start_date,
        pace=pace, room_preference=room_pref
    )
    total_cost = sum(day['cost'] for day in result['itinerary'])
    st.session_state.itinerary = result['itinerary']
    st.session_state.result = result
    st.session_state.total_cost = total_cost
    st.session_state.budget = budget
    st.session_state.trip_days = trip_days
    st.session_state.num_people = num_people

# Display results if available
if st.session_state.itinerary is not None:
    itinerary = st.session_state.itinerary
    result = st.session_state.result
    hotel = result['hotel']
    hotel_backup = result['hotel_backup']
    restaurants = result['restaurants']
    restaurant_backups = result['restaurant_backups']
    attractions = result['attractions']
    attraction_backups = result['attraction_backups']
    beach = result['beach']
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
        per_person_cost = total_cost / num_people if num_people > 0 else total_cost
        st.markdown(f'<div class="metric-card"><h4>Per Person</h4><p style="font-size:1.8rem; font-weight:700; color:#FFD93D;">${per_person_cost:,.0f}</p></div>', unsafe_allow_html=True)
    with col4:
        per_person_budget = budget / num_people if num_people > 0 else budget
        st.markdown(f'<div class="metric-card"><h4>Budget/Person</h4><p style="font-size:1.8rem; font-weight:700; color:#9B5DE5;">${per_person_budget:,.0f}</p></div>', unsafe_allow_html=True)
    with col5:
        remaining = max(0, budget - total_cost)
        over = max(0, total_cost - budget)
        color = "#2C3E50" if remaining > 0 else "#FF6B6B"
        label = f"+${over:,.0f}" if over > 0 else f"-${remaining:,.0f}"
        st.markdown(f'<div class="metric-card"><h4>{"Remaining" if remaining > 0 else "Over by"}</h4><p style="font-size:1.8rem; font-weight:700; color:{color};">{label}</p></div>', unsafe_allow_html=True)
    
    if budget > 0:
        ratio = min(total_cost / budget, 1.0)
        st.progress(ratio)
        st.caption(f"📊 You're using {min(total_cost/budget*100, 100):.1f}% of your budget")
    else:
        st.progress(0)
        st.caption("📊 Budget not set — cost shown as estimate")
    
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
        day_idx = day['day'] - 1
        zone_name = ""
        if day_idx < len(attraction_backups) and attraction_backups[day_idx]:
            zone_name = day['activities'][0].get('neighborhood', '') if day['activities'] else ''
        exp_label = f"Day {day['day']} – {day['date']}{' · ' + zone_name if zone_name else ''}  (${day['cost']:,.0f})"
        with st.expander(exp_label, expanded=True):
            col1, col2 = st.columns([2,1])
            with col1:
                st.markdown(f"**🏨 Hotel:** {day['hotel']['name']}")
                st.markdown("**📋 Activities:**")
                for act in day['activities']:
                    nb = act.get('neighborhood', '')
                    dist = act.get('distance_from_hotel', '')
                    extras = f"📍 {nb}" if nb else ""
                    extras += f" ({dist}km from hotel)" if dist else ""
                    st.write(f"• {act['time']} – {act['name']} ({act['duration']}) – ${act['cost']}{extras}")
                st.markdown("**🍽️ Meals:**")
                for meal in day['meals']:
                    st.write(f"• {meal['time']} – {meal['name']} – ${meal['cost']}")
                # Plan B
                backup = attraction_backups[day_idx] if day_idx < len(attraction_backups) else None
                if backup:
                    st.markdown("**🔄 Plan B (if needed):**")
                    st.write(f"• {backup['name']} ({backup['duration']}h) – ${backup['price']} 📍 {backup.get('neighborhood', '')}")
            with col2:
                st.markdown("**🚗 Transport:**")
                for t in day['transport']:
                    st.write(f"• {t['mode']} – ${t['cost']:.1f}/person")
                st.markdown("**💰 Breakdown (per person):**")
                hotel_pp = day['hotel']['price'] / num_people
                st.write(f"Accommodation: ${hotel_pp:.2f}")
                st.write(f"Activities: ${sum(a['cost'] for a in day['activities'])}")
                st.write(f"Meals: ${sum(m['cost'] for m in day['meals'])}")
                st.write(f"Transport: ${sum(t['cost'] for t in day['transport']):.1f}")
                st.write(f"**Per person: ${day['cost_per_person']:.2f}**")
                st.write(f"**Group total: ${day['cost']:.2f}**")
    
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
    budget_hotels = [h for h in CURATED_HOTELS if h['price'] <= budget/trip_days * 1.5] if budget>0 else CURATED_HOTELS
    if not budget_hotels:
        budget_hotels = CURATED_HOTELS[:3]
    show_hotels = budget_hotels[:2] + ([hotel_backup] if hotel_backup not in budget_hotels[:2] and hotel_backup != hotel else [])[:1]
    show_hotels = show_hotels[:3]
    cols = st.columns(min(3, len(show_hotels)))
    for i, h in enumerate(show_hotels):
        tag = " ✅ YOUR PICK" if h['name'] == hotel['name'] else " 🔄 Plan B" if h['name'] == hotel_backup['name'] else ""
        with cols[i]:
            st.markdown(f"""
            <div class="hotel-card">
                <h4>{h['name']}{tag}</h4>
                <p>📍 {h.get('neighborhood', 'Miami, FL')}</p>
                <p>⭐ {h['stars']}/5</p>
                <p>💰 ${h['price']}/night</p>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown('<div class="section-title">🍽️ Recommended Restaurants (match your budget)</div>', unsafe_allow_html=True)
    affordable = [r for r in CURATED_RESTAURANTS if r['price'] <= (budget/trip_days)*0.5] if budget>0 else CURATED_RESTAURANTS
    if not affordable:
        affordable = CURATED_RESTAURANTS[:3]
    show_rests = restaurants + restaurant_backups[:3 - len(restaurants)]
    cols = st.columns(min(3, len(show_rests)))
    for i, r in enumerate(show_rests):
        tag = " ✅ SELECTED" if r in restaurants else " 🔄 Plan B"
        with cols[i]:
            st.markdown(f"""
            <div class="rest-card">
                <h4>{r['name']}{tag}</h4>
                <p>🍽️ {r['cuisine']}</p>
                <p>💰 ${r['price']}/person</p>
                <p>⭐ {r['rating']}/5</p>
                <p>📍 {r.get('neighborhood', 'Miami, FL')}</p>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown('<div class="section-title">📍 Top Attractions (based on your interests)</div>', unsafe_allow_html=True)
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
                <p>📍 {attr.get('neighborhood', 'Miami, FL')}</p>
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