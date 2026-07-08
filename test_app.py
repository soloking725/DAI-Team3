import sys
sys.path.insert(0, '/Users/promiseegunjobi/Documents/GitHub/DAI-Team3')
from app import generate_curated_itinerary
from datetime import datetime

try:
    result = generate_curated_itinerary(
        num_people=2,
        budget=2000,
        trip_days=3,
        selected_activities=["Beach", "Sightseeing"],
        selected_transit=["Walking", "Ride‑share (Uber/Lyft)"],
        start_date=datetime.now(),
        pace="Moderate",
        room_preference="Shared"
    )
    print("✅ Function ran successfully!")
    print(f"Itinerary days: {len(result['itinerary'])}")
    print(f"Hotel: {result['hotel']['name']}")
    print(f"Restaurants: {len(result['restaurants'])}")
    total = sum(day['cost'] for day in result['itinerary'])
    print(f"Total cost: ${total:.0f}")
    for day in result['itinerary']:
        print(f"  Day {day['day']}: {len(day['activities'])} activities, ${day['cost']:.0f}")
except Exception as e:
    print(f"❌ ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
