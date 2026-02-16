# models/nation.py

class Nation:
    def __init__(self, name: str, year: int, population: int, gdp: float, military_strength: float, political_stability: float, briefing: str = "", save_name: str = "default", treasury: float = None, world_gdp: dict = None, world_military: dict = None, stat_history: list = None):
        self.name = name
        self.save_name = save_name
        self.starting_year = year 
        self.briefing_text = briefing
        
        self.population = population
        self.public_approval = 50.0  
        self.gdp = gdp    
        self.treasury = treasury if treasury is not None else (gdp * 0.20)   
        self.national_debt = 0.0
        self.inflation_rate = 2.0    
        self.military_strength = military_strength
        self.political_stability = political_stability
        # --- NEW: World Leaderboards ---
        self.world_gdp = world_gdp if world_gdp is not None else {}
        self.world_military = world_military if world_military is not None else {}
        # --- NEW: Statistical History ---
        self.stat_history = stat_history if stat_history is not None else []
        
        self.intelligence_budget = 5.0 
        self.espionage_network = 50.0  
        
        self.factions = {} 
        self.history = [] 
    
    def record_stats(self, current_year):
        """Snapshots the nation's core statistics for charting."""
        self.stat_history.append({
            "Year": current_year,
            "GDP ($B)": round(self.gdp, 2),
            "Treasury ($B)": round(self.treasury, 2),
            "Stability (%)": round(self.political_stability, 1),
            "Approval (%)": round(self.public_approval, 1),
            "Population": self.population
        })

    def add_event(self, year: int, directive: str):
        self.history.append({"year": year, "directive": directive})

    def to_dict(self):
        """Converts stats into a dictionary. We must include 'save_name' here."""
        return {
            "name": self.name,
            "save_name": self.save_name, # Added this
            "starting_year": self.starting_year,
            "briefing_text": self.briefing_text,
            "population": self.population,
            "public_approval": self.public_approval,
            "gdp": self.gdp,
            "treasury": self.treasury,
            "world_gdp": self.world_gdp,
            "world_military": self.world_military,
            "stat_history": self.stat_history, # Add this!
            "military_strength": self.military_strength,
            "political_stability": self.political_stability,
            "intelligence_budget": self.intelligence_budget,
            "espionage_network": self.espionage_network,
            "factions": self.factions,
            "history": self.history
        }

    @classmethod
    def from_dict(cls, data):
        """Rebuilds the nation from a dictionary. We retrieve 'save_name' here."""
        nation = cls(
            name=data["name"],
            save_name=data.get("save_name", "default"), # Retrieve the save name
            year=data.get("starting_year", 1),
            population=data["population"],
            gdp=data["gdp"],
            treasury=data.get("treasury", data["gdp"] * 0.20), # Add this!
            world_gdp=data.get("world_gdp", {}),
            stat_history=data.get("stat_history", []), # Add this!
            world_military=data.get("world_military", {}),
            military_strength=data["military_strength"],
            political_stability=data["political_stability"],
            briefing=data.get("briefing_text", "")
        )
        nation.public_approval = data.get("public_approval", 50.0)
        nation.intelligence_budget = data.get("intelligence_budget", 5.0)
        nation.espionage_network = data.get("espionage_network", 50.0)
        nation.factions = data.get("factions", {})
        nation.history = data.get("history", [])
        return nation

    def display_briefing(self):
        print(f"\n==================================================")
        print(f" INITIAL CABINET REPORT: {self.name.upper()} ")
        print(f"==================================================")
        print(f"{self.briefing_text}\n")
        print(f"--- National Statistics ---")
        print(f"Population: {self.population:,}")
        print(f"GDP: ${self.gdp:,.2f}B")
        print(f"Military Strength Score: {self.military_strength:,.1f}")
        print(f"Political Stability: {self.political_stability:,.1f}/100")
        print(f"Public Approval: {self.public_approval:,.1f}%")
        print("\n-- Internal Faction Support --")
        if not self.factions:
            print("No major factions have mobilized yet.")
        else:
            for faction, support in self.factions.items():
                print(f" * {faction}: {support:.1f}/100")
        print("-" * 50)

    def process_turn(self):
        from systems.simulation import simulate_population, simulate_economy, resolve_internal_stability
        print("\nSimulating internal events and faction actions...")
        turn_events = resolve_internal_stability(self)
        pop_growth = simulate_population(self)
        gdp_growth, ggr = simulate_economy(self)

        # --- NEW: Collect Annual Taxes (e.g., 15% of GDP) ---
        tax_revenue = self.gdp * 0.15
        self.treasury += tax_revenue

        # Background simulation for the rest of the world
        import random
        for country in self.world_gdp:
            self.world_gdp[country] *= random.uniform(1.01, 1.04) # 1% to 4% global GDP growth
        for country in self.world_military:
            self.world_military[country] *= random.uniform(0.98, 1.02) # Military power fluctuates
        
        print("\n=== End of Year Report ===")
        if turn_events:
            print("Notable Events:")
            for event in turn_events:
                print(f" * {event}")
        print("-" * 26)
        print(f"Population Change: +{pop_growth:,} citizens")
        print(f"Economic Growth Rate: {ggr * 100:.2f}%")
        print(f"Total GDP Change: ${gdp_growth:,.2f}B")
        print(f"Tax Revenue Collected: +${tax_revenue:,.2f}B")
        print("==========================\n")