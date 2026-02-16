# systems/events.py

def trigger_historical_event(nation, year, ai_handler):
    """
    Triggers a real-world historical event based on the current year.
    Ceases all events if the year reaches 2026.
    """
    if year >= 2026:
        print(f"\n[SYSTEM LOG]: Year {year} reached. Historical event feeding deactivated.")
        return None

    print(f"\n[CHRONICLE]: Retrieving historical data for the year {year}...")
    
    # The AI now acts as the historian
    event_report = ai_handler.generate_event(nation, year)
    
    return event_report