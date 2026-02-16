# systems/stat_extractor.py
import re

def apply_ai_stats(nation, ai_report):
    """
    Parses the AI report, extracts statistical and factional changes, and applies them.
    """
    # --- THE SYSTEM VALIDATION FAILSAFE ---
    # If the report is empty, or doesn't have the required sections, abort safely.
    if not ai_report or not isinstance(ai_report, str) or "Statistical Updates:" not in ai_report:
        print("[SYSTEM LOG]: Extraction aborted - No valid stats section found (AI Error or Rate Limit).")
        return

    print("\n[SYSTEM LOG]: Extracting statistical data from AI report...")
    
    # --- 1. CORE STATS EXTRACTION ---
    try:
        stats_section = ai_report.split("Statistical Updates:")[1].split("Factional Reactions:")[0]
        pattern = r'([A-Za-z\s]+):\s*([+-]?\d+(?:\.\d+)?)(%?)'
        matches = re.findall(pattern, stats_section)
        
        if matches:
            for stat_name, value_str, is_percentage in matches:
                stat_name = stat_name.strip().lower()
                value = float(value_str)
                
                if "gdp" in stat_name:
                    if is_percentage:
                        change = nation.gdp * (value / 100)
                        nation.gdp += change
                    else:
                        nation.gdp += value
                
                elif "treasury" in stat_name:
                    if is_percentage:
                        change = nation.treasury * (value / 100)
                        nation.treasury += change
                    else:
                        nation.treasury += value
                        
                elif "population" in stat_name:
                    if is_percentage:
                        change = nation.population * (value / 100)
                        nation.population += int(change)
                    else:
                        nation.population += int(value)
                        
                elif "military" in stat_name:
                    change = nation.military_strength * (value / 100) if is_percentage else value
                    nation.military_strength += change
                    
                elif "stability" in stat_name:
                    nation.political_stability = max(0.0, min(100.0, nation.political_stability + value))
                    
                elif "approval" in stat_name:
                    nation.public_approval = max(0.0, min(100.0, nation.public_approval + value))
        else:
            print("[SYSTEM LOG]: No valid core stat changes found.")
            
    except Exception as e:
        print(f"[SYSTEM LOG]: Core extraction failed: {str(e)}")


    # --- 2. FACTIONAL SUPPORT EXTRACTION ---
    if "Factional Reactions:" in ai_report:
        print("\n[SYSTEM LOG]: Extracting factional shifts...")
        try:
            factions_section = ai_report.split("Factional Reactions:")[1]
            
            # Safely handle if the global reactions section is missing
            if "Global Reactions Simulated:" in factions_section:
                factions_section = factions_section.split("Global Reactions Simulated:")[0]
                
            faction_pattern = r'([A-Za-z\s]+):.*?\(\s*Support Change:\s*([+-]?\d+(?:\.\d+)?)\s*\)'
            faction_matches = re.findall(faction_pattern, factions_section)
            
            if faction_matches:
                for faction_name, value_str in faction_matches:
                    faction_name = faction_name.strip()
                    value = float(value_str)
                    
                    if faction_name not in nation.factions:
                        nation.factions[faction_name] = 50.0
                        
                    nation.factions[faction_name] += value
                    nation.factions[faction_name] = max(0.0, min(100.0, nation.factions[faction_name]))
                    
        except Exception as e:
            print(f"[SYSTEM LOG]: Faction extraction failed: {str(e)}")