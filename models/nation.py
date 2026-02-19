# models/nation.py
import random

class Nation:
    def __init__(self, name: str, year: int, population: int, gdp: float, military_strength: float, political_stability: float, briefing: str = "", save_name: str = "default", treasury: float = None, world_gdp: dict = None, world_military: dict = None, stat_history: list = None, flag_emoji: str = "🏳️", industrialization_level: int = 1, tech_level: int = 1, nation_era: str = "Stone Age", regional_neighbors: dict = None):
        self.name = name
        self.save_name = save_name
        self.starting_year = year 
        self.briefing_text = briefing
        self.flag_emoji = flag_emoji
        
        self.industrialization_level = industrialization_level
        self.tech_level = tech_level
        self.nation_era = nation_era
            
        self.population = population
        self.public_approval = 50.0  
        self.gdp = gdp    
        self.treasury = treasury if treasury is not None else (gdp * 0.20)   
        self.military_strength = military_strength
        self.political_stability = political_stability
        
        self.world_gdp = world_gdp if world_gdp is not None else {}
        self.world_military = world_military if world_military is not None else {}
        
        # --- NEW: THEATER OF OPERATIONS ---
        self.regional_neighbors = regional_neighbors if regional_neighbors is not None else {}
        
        self.stat_history = stat_history if stat_history is not None else []
        self.history = [] 

    @property
    def gdp_per_capita(self):
        if self.population <= 0: return 0
        return (self.gdp * 1_000_000_000) / self.population

    @property
    def combat_power(self):
        """Calculates true military power based on HOI4-style tech and stability multipliers."""
        tech_modifier = 1 + (self.tech_level * 0.20)
        ind_modifier = 1 + (self.industrialization_level * 0.20)
        stability_modifier = max(0.1, self.political_stability / 100.0) # Prevents multiplying by 0
        return self.military_strength * tech_modifier * ind_modifier * stability_modifier

    def update_era(self):
        gdp_pc = self.gdp_per_capita
        if self.tech_level == 5 and self.industrialization_level == 5 and gdp_pc > 30000:
            self.nation_era = "Space Age"
        elif self.tech_level >= 5 and self.industrialization_level >= 4:
            self.nation_era = "Cyber Age"
        elif self.tech_level >= 4 and self.industrialization_level >= 3:
            self.nation_era = "Industrialization Age"
        elif self.tech_level >= 3 and self.industrialization_level >= 2:
            self.nation_era = "Steel Age"
        elif self.tech_level >= 2 and self.industrialization_level >= 2 and self.political_stability >= 40:
            self.nation_era = "Iron Age"
        elif self.tech_level >= 1 and gdp_pc > 500:
            self.nation_era = "Mythic Age"
        elif self.industrialization_level >= 2:
            self.nation_era = "Bronze Age"
        else:
            self.nation_era = "Stone Age"

    def execute_war(self, target_name, target_base_strength, force_commitment_pct):
        """Python resolves the war deterministically using a slight RNG dice roll."""
        # Player allocates forces
        player_committed_power = self.combat_power * (force_commitment_pct / 100.0)
        
        # We assume the enemy fights at 100% capacity to defend their homeland.
        # We give them a randomized Tech/Ind level based on the player's era.
        enemy_tech_mod = 1 + (random.randint(max(1, self.tech_level-1), min(5, self.tech_level+1)) * 0.20)
        enemy_combat_power = target_base_strength * enemy_tech_mod
        
        # The Dice Roll (Adds slight unpredictability, like terrain or generalship)
        player_roll = player_committed_power * random.uniform(0.85, 1.15)
        enemy_roll = enemy_combat_power * random.uniform(0.85, 1.15)
        
        # Calculate War Costs
        war_cost_gdp = self.gdp * (force_commitment_pct / 200.0) # War is expensive!
        self.treasury -= war_cost_gdp
        
        if player_roll > enemy_roll:
            result = "VICTORY"
            # Spoils of war: Annex territory (Population and GDP boost)
            self.gdp += target_base_strength * 0.5
            self.population += int(target_base_strength * 10000)
            self.military_strength -= (self.military_strength * 0.05) # Light casualties
            self.political_stability += 5.0
            self.public_approval += 10.0
        else:
            result = "DEFEAT"
            # Disastrous losses
            self.military_strength -= (self.military_strength * (force_commitment_pct / 100.0) * 0.5) 
            self.political_stability -= 15.0
            self.public_approval -= 20.0
            
        return {
            "result": result,
            "player_power": int(player_roll),
            "enemy_power": int(enemy_roll),
            "cost_billions": war_cost_gdp
        }

    def process_turn(self):
        self.update_era()

    def record_stats(self, year):
        self.stat_history.append({
            "Year": year,
            "Population": self.population,
            "GDP ($B)": self.gdp,
            "Treasury ($B)": self.treasury,
            "Stability (%)": self.political_stability,
            "Approval (%)": self.public_approval,
            "Military": self.military_strength,
            "Tech Level": self.tech_level,
            "Ind Level": self.industrialization_level
        })

    def add_event(self, year, summary, law_impact="None", event="None"):
        self.history.append({"year": year, "summary": summary, "law_impact": law_impact, "event": event})

    def to_dict(self):
        return {
            "name": self.name,
            "save_name": self.save_name,
            "starting_year": self.starting_year,
            "briefing_text": self.briefing_text,
            "flag_emoji": self.flag_emoji,
            "industrialization_level": self.industrialization_level,
            "tech_level": self.tech_level,
            "nation_era": self.nation_era,
            "population": self.population,
            "public_approval": self.public_approval,
            "gdp": self.gdp,
            "treasury": self.treasury,
            "world_gdp": self.world_gdp,
            "world_military": self.world_military,
            "regional_neighbors": self.regional_neighbors,
            "stat_history": self.stat_history,
            "military_strength": self.military_strength,
            "political_stability": self.political_stability,
            "history": self.history
        }

    @classmethod
    def from_dict(cls, data):
        nation = cls(
            name=data["name"],
            save_name=data.get("save_name", "default"),
            year=data.get("starting_year", 1),
            flag_emoji=data.get("flag_emoji", "🏳️"),
            industrialization_level=data.get("industrialization_level", 1),
            tech_level=data.get("tech_level", 1),
            nation_era=data.get("nation_era", "Stone Age"),
            population=data["population"],
            gdp=data["gdp"],
            treasury=data.get("treasury", data["gdp"] * 0.20), 
            world_gdp=data.get("world_gdp", {}),
            stat_history=data.get("stat_history", []), 
            world_military=data.get("world_military", {}),
            regional_neighbors=data.get("regional_neighbors", {}),
            military_strength=data["military_strength"],
            political_stability=data["political_stability"],
            briefing=data.get("briefing_text", "")
        )
        nation.public_approval = data.get("public_approval", 50.0)
        nation.history = data.get("history", [])
        return nation