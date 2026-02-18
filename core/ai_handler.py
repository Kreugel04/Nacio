# core/ai_handler.py
import json
import time
import os
import re
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Define custom safety thresholds 
safety_settings = [
    types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
    types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
    types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
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
        clean_name = country_name.strip()
        lookup_key = f"{clean_name}-{year}"

        if os.path.exists(archive_path):
            with open(archive_path, "r") as f:
                archive = json.load(f)
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
                    if "world_gdp" not in data:
                        data["world_gdp"] = {"United States": 10000.0, "China": 1000.0, "Japan": 5000.0}
                    if "world_military" not in data:
                        data["world_military"] = {"United States": 950.0, "Russia": 800.0, "China": 700.0}
                    return data

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
        
        for model_name in ['gemini-2.5-flash', 'gemini-2.0-flash']:
            try:
                print(f"[SYSTEM LOG]: Attempting generation with {model_name}...")
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=system_prompt,
                    config=types.GenerateContentConfig(safety_settings=safety_settings)
                )
                
                match = re.search(r'(\{.*\})', response.text, re.DOTALL)
                if match:
                    data = json.loads(match.group(1))
                    new_clean_key = f"{clean_name}-{year}"
                    
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
                    time.sleep(5)
                    continue
                return f"[UPLINK ERROR]: {str(e)}"
        return None

    def parse_directive(self, directive_text, nation, turn_number):
        """Analyzes player directives with highly compressed token-optimized history."""
        history_text = "No prior history."
        if nation.history:
            compressed_turns = []
            for turn in nation.history[-3:]: 
                year = turn.get('year', 'Unknown Year')
                summary = turn.get('summary', 'General governance.')
                law_impact = turn.get('law_impact', 'Maintained status quo.')
                event = turn.get('event', 'No major global events.')
                stats = turn.get('stats', 'Negligible changes.')
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
                    time.sleep(5) 
                    continue
                return f"[UPLINK ERROR]: {str(e)}"
        
        return "[SYSTEM ERROR]: Maximum retries reached. The AI Cabinet is unavailable."
    
    def run_espionage(self, player_nation, target_nation, operation_details, turn_number):
        """Handles covert operations narrative."""
        system_prompt = f"Director of Intelligence report for {player_nation.name} against {target_nation}. Operation details: {operation_details}"
        
        for model_name in ['gemini-2.5-flash', 'gemini-2.0-flash']:
            try:
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=system_prompt,
                    config=types.GenerateContentConfig(safety_settings=safety_settings)
                )
                return response.text.strip()
            except Exception as e:
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    print(f"\n[SYSTEM LOG]: {model_name} overloaded. Swapping models...")
                    time.sleep(2)
                    continue
                return f"[INTELLIGENCE ERROR]: {str(e)}"
        return "[INTELLIGENCE ERROR]: Operatives unreachable due to communication blackout."

    def negotiate(self, player_nation_name, target_nation, player_message, chat_history):
        """Acts as a foreign delegate for diplomatic negotiations."""
        history_text = ""
        for sender, msg in chat_history:
            history_text += f"{sender}: {msg}\n"
            
        system_prompt = f"""
        You are the Chief Diplomat representing {target_nation}.
        You are currently in a secure negotiation with the Supreme Leader of {player_nation_name}.
        
        Previous Conversation Context:
        {history_text}
        
        Supreme Leader of {player_nation_name} says: "{player_message}"
        
        Respond in character as the diplomat of {target_nation}. Be strategic, realistic, and protective of your own nation's interests. Keep the response to 1 or 2 paragraphs.
        """
        
        for model_name in ['gemini-2.5-flash', 'gemini-2.0-flash']:
            try:
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=system_prompt,
                    config=types.GenerateContentConfig(safety_settings=safety_settings)
                )
                return response.text.strip()
            except Exception as e:
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    print(f"\n[SYSTEM LOG]: {model_name} overloaded. Swapping models...")
                    time.sleep(2)
                    continue
                return f"[COMMUNICATIONS SEVERED]: {str(e)}"
        return "[COMMUNICATIONS SEVERED]: The foreign delegation is unreachable."

    def generate_event(self, nation, year):
        """Generates a significant historical event with model failover."""
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
        
        for model_name in ['gemini-2.5-flash', 'gemini-2.0-flash']:
            try:
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=system_prompt,
                    config=types.GenerateContentConfig(safety_settings=safety_settings)
                )
                return response.text.strip()
                
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                    print(f"\n[SYSTEM LOG]: {model_name} overloaded. Swapping models...")
                    time.sleep(2)
                    continue
                else:
                    return f"[HISTORICAL CHRONICLER ERROR]: {error_msg}"
                    
        return "### GLOBAL EVENT DELAYED\nDue to dense fog of war and global communications gridlock, this year's historical events remain unrecorded. The simulation continues."