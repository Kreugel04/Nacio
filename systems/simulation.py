# systems/simulation.py

def simulate_population(nation):
    """
    Calculates population growth based on the game document formula[cite: 45].
    """
    # Base annual percentage (e.g., 1.0%) [cite: 39]
    pgr_base = 0.010  
    
    # Grabbing factors (defaulting to 1.0 if they don't exist yet) [cite: 40-44]
    hf = getattr(nation, 'healthcare_factor', 1.0)
    ef = getattr(nation, 'education_factor', 1.0)
    fsf = getattr(nation, 'food_security_factor', 1.0)
    qlf = getattr(nation, 'quality_of_life_factor', 1.0)
    pm_pop = getattr(nation, 'policy_multiplier_pop', 1.0)
    
    # The Formula [cite: 45]
    growth_rate = pgr_base * hf * ef * fsf * qlf * pm_pop
    
    new_population = int(nation.population * (1 + growth_rate))
    growth_amount = new_population - nation.population
    
    # Apply to nation
    nation.population = new_population
    return growth_amount

def simulate_economy(nation):
    """
    Calculates GDP growth[cite: 48].
    Simplified for turn 1 to use a base rate modified by political stability.
    """
    base_growth = 0.025 # 2.5% base global growth assumption
    
    # Political stability affects growth (High stability = bonus, low = penalty) [cite: 34]
    stability_modifier = (nation.political_stability - 50) / 1000 
    
    ggr = base_growth + stability_modifier
    
    new_gdp = nation.gdp * (1 + ggr)
    growth_amount = new_gdp - nation.gdp
    
    # Apply to nation
    nation.gdp = new_gdp
    return growth_amount, ggr

# Add this to the bottom of systems/simulation.py

def resolve_internal_stability(nation):
    """
    Evaluates faction support and public approval to generate end-of-turn events 
    like protests or economic booms [cite: 88-89, 93].
    """
    events_triggered = []
    
    # 1. Check for angry factions (Support under 40)
    angry_factions = [faction for faction, support in nation.factions.items() if support < 40]
    
    if angry_factions:
        print("\n[CRITICAL ALERT]: Internal Factional Unrest Detected!")
        for faction in angry_factions:
            print(f" -> The {faction} is organizing strikes and lobbying against your regime!")
            # Punish stability and economy
            nation.political_stability -= 2.0
            economic_damage = nation.gdp * 0.005 # 0.5% GDP loss from strikes
            nation.gdp -= economic_damage
            events_triggered.append(f"{faction} Strikes (-${economic_damage:,.2f}B GDP)")
            
    # 2. Check for ecstatic factions (Support over 80)
    happy_factions = [faction for faction, support in nation.factions.items() if support > 80]
    for faction in happy_factions:
        print(f"\n[FACTION BOON]: The {faction} is rallying massive public support for your agenda!")
        nation.political_stability += 1.0

    # 3. Check general Public Approval extremes
    if nation.public_approval < 30:
        print("\n[CRITICAL ALERT]: Widespread civil unrest! The general public is revolting.")
        nation.political_stability -= 5.0
        events_triggered.append("Civil Unrest")
    elif nation.public_approval > 80:
        print("\n[NATIONAL BOOM]: Unprecedented public trust is driving national efficiency!")
        economic_boost = nation.gdp * 0.01
        nation.gdp += economic_boost
        events_triggered.append(f"Economic Boom (+${economic_boost:,.2f}B GDP)")
        
    # Cap stability between 0 and 100
    nation.political_stability = max(0.0, min(100.0, nation.political_stability))
    
    return events_triggered

# Add to the bottom of systems/simulation.py