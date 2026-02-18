# core/ai_handler.py
import json
import time
import os
import re
from dotenv import load_dotenv
from google import genai        # The new SDK
from google.genai import types  # For safety and config types

# 1. Define custom safety thresholds using the new SDK types
safety_settings = [
    types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
    types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
    types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
    # Keep NSFW content blocked for professional integrity
    types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_ONLY_HIGH"),
]

class AIHandler:
    def __init__(self):
        """Initializes the AI connection using the API key from the .env file."""
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        
        if not api_key:
            raise ValueError("API Key not found! Please check your .env file.")
            
        self.client = genai.Client(api_key=api_key)
    
    def generate_starting_nation(self, country_name, year):
        """Asks the AI for stats, with key normalization and world rank failovers."""
        archive_path = "historical_archive.json"
        
        # --- NORMALIZATION ---
        # Strip spaces to ensure "Philippines -1950" matches "Philippines-1950"
        clean_name = country_name.strip()
        lookup_key = f"{clean_name}-{year}"

        # 1. Check the local archive first
        if os.path.exists(archive_path):
            with open(archive_path, "r") as f:
                archive = json.load(f)
                
                # Fuzzy Search: Check for exact match OR space-stripped match
                found_key = None
                if lookup_key in archive:
                    found_key = lookup_key
                else:
                    for existing_key in archive.keys():
                        if existing_key.replace(" ", "") == lookup_key.replace(" ", ""):
                            found_key = existing_key
                            break
                
                if found_key:
                    print(f"[SYSTEM LOG]: Match found! Loading {found_key}...")
                    data = archive[found_key]
                    
                    # --- DATA INTEGRITY FAILOVER ---
                    # Ensure older archive entries (missing world data) don't crash the UI
                    if "world_gdp" not in data:
                        data["world_gdp"] = {"United States": 10000.0, "China": 1000.0, "Japan": 5000.0}
                    if "world_military" not in data:
                        data["world_military"] = {"United States": 950.0, "Russia": 800.0, "China": 700.0}
                    
                    return data

        # 2. If not in archive, proceed to AI Generation
        print(f"[SYSTEM LOG]: {lookup_key} not in archives. Requesting AI generation...")
        
        system_prompt = f"""
        You are the world-building engine for 'Nacio: A Global Symphony'.
        Leader: {country_name}, Year: {year}.
        
        Provide realistic starting statistics based on real historical data for {year}.
        Generate the Top 10 highest GDPs and Top 10 Militaries in the world for {year} (exclude {country_name}).
        Write a 2-paragraph 'Initial Cabinet Report' on the immediate challenges.
        
        Respond ONLY in valid JSON format using this exact schema:
        {{
            "population": [integer],
            "gdp": [float, in billions USD],
            "military_strength": [float, 0-1000 scale],
            "political_stability": [float, 0-100 scale],
            "briefing": "[narrative text]",
            "world_gdp": {{"Country": value}},
            "world_military": {{"Country": value}}
        }}
        """
        
        # --- MODEL FAILOVER LOOP ---
        for model_name in ['gemini-2.5-flash', 'gemini-2.0-flash']:
            try:
                print(f"[SYSTEM LOG]: Attempting generation with {model_name}...")
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=system_prompt,
                    config=types.GenerateContentConfig(safety_settings=safety_settings)
                )
                
                # --- ROBUST JSON EXTRACTION ---
                match = re.search(r'(\{.*\})', response.text, re.DOTALL)
                if match:
                    data = json.loads(match.group(1))
                    
                    # Standardize the new entry before saving to prevent future space bugs
                    new_clean_key = f"{clean_name}-{year}"
                    
                    # Save to archive
                    if not os.path.exists(archive_path):
                        with open(archive_path, "w") as f: json.dump({}, f)
                    with open(archive_path, "r+") as f:
                        archive = json.load(f)
                        archive[new_clean_key] = data
                        f.seek(0); json.dump(archive, f, indent=4); f.truncate()
                    
                    return data
            except Exception as e:
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    print(f"[ALERT]: {model_name} congested. Waiting 5s then swapping...")
                    time.sleep(5) # Give the server a breather!
                    continue
                return f"[UPLINK ERROR]: {str(e)}"
        
        return None

    def parse_directive(self, directive_text, nation, turn_number):
        """Analyzes player directives with highly compressed token-optimized history."""
        
        # --- CONTEXT COMPRESSION ENGINE ---
        history_text = "No prior history."
        if nation.history:
            compressed_turns = []
            # Only pull the last 3 years to save massive amounts of tokens
            for turn in nation.history[-3:]: 
                # We use .get() so it doesn't crash if an old save doesn't have these exact keys yet
                year = turn.get('year', 'Unknown Year')
                summary = turn.get('summary', 'General governance.')
                law_impact = turn.get('law_impact', 'Maintained status quo.')
                event = turn.get('event', 'No major global events.')
                stats = turn.get('stats', 'Negligible changes.')
                
                # The ultra-dense, token-saving format you requested
                turn_str = f"[{year}] Summary: {summary} | Law/Impact: {law_impact} | Event: {event} | Stats: {stats}"
                compressed_turns.append(turn_str)
            
            history_text = "\n".join(compressed_turns)

        system_prompt = f"""
        You are the simulation engine for 'Nacio'. Lead: {nation.name}, Year: {turn_number}.
        
        --- RECENT CONDENSED HISTORY ---
        {history_text}
        --------------------------------
        
        New Directive: "{directive_text}"
        
        Analyze outcomes and statistical updates (Population, GDP, Treasury, Military Strength, Stability, Approval).
        Format the response clearly using Markdown.
        """    
        for model_name in ['gemini-2.5-flash', 'gemini-2.0-flash']:
            try:
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=system_prompt,
                    config=types.GenerateContentConfig(safety_settings=safety_settings)
                )
                if response.text:
                    return response.text.strip()
            except Exception as e:
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    print(f"[ALERT]: {model_name} congested. Waiting 5s then swapping...")
                    time.sleep(5) # Give the server a breather!
                    continue
                return f"[UPLINK ERROR]: {str(e)}"
        
        return "[SYSTEM ERROR]: Maximum retries reached. The AI Cabinet is unavailable."
    

    def run_espionage(self, player_nation, target_nation, operation_details, turn_number):
        """Handles covert operations narrative."""
        system_prompt = f"Director of Intelligence report for {player_nation.name} against {target_nation}..."
        
        try:
            response = self.client.models.generate_content(
                model='gemini-2.0-flash',
                contents=system_prompt,
                config=types.GenerateContentConfig(safety_settings=safety_settings)
            )
            return response.text.strip()
        except Exception as e:
            return f"[INTELLIGENCE ERROR]: {str(e)}"
        

    def generate_event(self, nation, year):
        """Generates a significant historical event with auto-retry for API rate limits."""
        if year >= 2026: return None
        
        system_prompt = f"""
        Identify a SIGNIFICANT REAL-WORLD HISTORICAL EVENT that occurred in {year}.
        Analyze how this event specifically impacts {nation.name}.
        
        Output format:
        Event Title: [Official Historical Name]
        Historical Context: [2-3 sentences explaining the global situation in {year}]
        Impact on {nation.name}: [How this specifically affects the player's country]
        
        Statistical Updates:
        [Stat Name]: [Change, e.g., -5% or +10.0]
        """
        
        max_retries = 2
        for attempt in range(max_retries):
            try:
                # We stick to the primary model here, as events need good historical context
                response = self.client.models.generate_content(
                    model='gemini-2.0-flash',
                    contents=system_prompt,
                    config=types.GenerateContentConfig(safety_settings=safety_settings)
                )
                return response.text.strip()
                
            except Exception as e:
                error_msg = str(e)
                # If Google tells us to wait, we actually wait!
                if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                    print(f"\n[SYSTEM LOG]: Global Event API overloaded. Waiting 50 seconds before retrying...")
                    time.sleep(50) # The API specifically requested a ~48s wait
                    continue
                else:
                    return f"[HISTORICAL CHRONICLER ERROR]: {error_msg}"
                    
        return "### GLOBAL EVENT DELAYED\nDue to dense fog of war and global communications gridlock, this year's historical events remain unrecorded. The simulation continues."