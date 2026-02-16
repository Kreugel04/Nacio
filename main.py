# main.py
from models.nation import Nation
from core.engine import GameEngine
from core.ai_handler import AIHandler

def create_dynamic_nation():
    """Prompts the user for any country and year, and uses AI to generate it."""
    print("Welcome to the Global Sandbox.")
    country = input("Enter the Nation you wish to lead (e.g., France, Roman Empire, Brazil): ").strip()
    year = input("Enter the starting year (e.g., 1914, -27, 2026): ").strip()
    
    # We need a temporary AI handler just to build the world
    builder_ai = AIHandler()
    nation_data = builder_ai.generate_starting_nation(country, year)
    
    if nation_data:
        return Nation(
            name=country,
            year=int(year),
            population=nation_data["population"],
            gdp=nation_data["gdp"],
            military_strength=nation_data["military_strength"],
            political_stability=nation_data["political_stability"],
            briefing=nation_data["briefing"]
        )
    else:
        print("Failed to generate nation. Falling back to default United States 1980.")
        return Nation("United States", 1980, 226000000, 2859.0, 960.0, 85.0, "Standard fallback simulation.")

def start_game():
    print("=========================================")
    print("  Welcome to Nacio: A Global Symphony")
    print("=========================================\n")
    
    # If they want to load a game immediately, let's give them the option
    load_choice = input("Type 'load' to resume a saved game, or press Enter to start a new simulation: ").strip().lower()
    
    if load_choice == 'load':
        # Create a dummy nation just to boot the engine, then force a load
        dummy_nation = Nation("Load", 1, 1, 1, 1, 1)
        engine = GameEngine(dummy_nation)
        engine.process_command("load")
        engine.run()
    else:
        player_nation = create_dynamic_nation()
        player_nation.display_briefing()
        
        engine = GameEngine(player_nation)
        engine.run()

if __name__ == "__main__":
    start_game()