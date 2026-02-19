# core/ai_handler.py
import json
import time
import os
import re
from dotenv import load_dotenv
from openai import OpenAI, RateLimitError

class AIHandler:
    def __init__(self):
        """Initializes the AI connection using OpenRouter via the OpenAI SDK."""
        load_dotenv()
        
        api_key = os.getenv("OPENROUTER_API_KEY") 
        if not api_key:
            raise ValueError("OpenRouter API Key not found! Please check your .env file.")
        
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
        
        # The exact Aurora Alpha Model ID
        self.model_name = "openrouter/aurora-alpha" 

    def _call_api(self, prompt, retries=2):
        """A centralized helper method to handle API calls, rate limits, and errors cleanly."""
        for attempt in range(retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7
                )
                return response.choices[0].message.content.strip()
                
            except RateLimitError:
                print(f"\n[SYSTEM LOG]: Aurora API rate limit hit. Waiting 5 seconds...")
                time.sleep(5)
                continue
            except Exception as e:
                return f"[UPLINK ERROR]: {str(e)}"
                
        return "[SYSTEM ERROR]: Maximum retries reached. The AI Cabinet is unavailable."

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
                    if "tech_level" not in data: data["tech_level"] = 1
                    if "industrialization_level" not in data: data["industrialization_level"] = 1
                    if "regional_neighbors" not in data: data["regional_neighbors"] = {}
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
            "flag_emoji": "[Provide the modern emoji flag for this country. If it is an ancient or fictional nation with no emoji, use 🏳️]",
            "population": [integer],
            "gdp": [float, in billions USD],
            "military_strength": [float, 0-1000 scale],
            "political_stability": [float, 0-100 scale],
            "industrialization_level": [integer 1-5 based on year and history],
            "tech_level": [integer 1-5 based on year and history],
            "briefing": "[narrative text]",
            "regional_neighbors": {{"Neighboring Country Name": [float, their military strength 0-1000 scale]}},
            "world_gdp": {{"Country": value}},
            "world_military": {{"Country": value}}
        }}
        """
        
        response_text = self._call_api(system_prompt)
        
        if "[UPLINK ERROR]" in response_text or "[SYSTEM ERROR]" in response_text:
            return response_text
            
        match = re.search(r'(\{.*\})', response_text, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(1))
                new_clean_key = f"{clean_name}-{year}"
                
                if not os.path.exists(archive_path):
                    with open(archive_path, "w") as f: json.dump({}, f)
                with open(archive_path, "r+") as f:
                    archive = json.load(f)
                    archive[new_clean_key] = data
                    f.seek(0); json.dump(archive, f, indent=4); f.truncate()
                
                return data
            except json.JSONDecodeError:
                return "[SYSTEM ERROR]: The AI provided an invalid data format."
                
        return "[SYSTEM ERROR]: Failed to extract data from the AI response."

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
        
        CRITICAL INSTRUCTION: You MUST respond in pure Markdown text. DO NOT output JSON, dictionaries, or code blocks.
        
        Use this EXACT format:
        ### Directive Analysis: [Short Title]
        
        **Narrative Impact:** [2-3 paragraphs explaining the political, economic, and social effects of the directive in a realistic, historical tone.]
        
        **Cabinet Reaction:**
        * **[Related Government Department]:** [Generate a reaction from a department depending on the context]
        
        **Global Reactions:**
        * **[Relevant Historical Nation]:** [Generate a diplomatic reaction based on the era]
        * **[Relevant Historical Faction/Alliance]:** [Generate a diplomatic response based on the era]
        
        **Statistical Impact:**
        * **Population:** [Change, e.g., +10000 or No Change]
        * **GDP:** [Change, e.g., +$1.5B or -$500M]
        * **Treasury:** [Change, e.g., -$2.0B or +$100M]
        * **Military Strength:** [Change, e.g., +10.0 or -5.0]
        * **Political Stability:** [Change, e.g., +5% or -2%]
        * **Public Approval:** [Change, e.g., +10% or -15%]
        * **Tech Level:** [Change, e.g., +1 or No Change]
        * **Ind Level:** [Change, e.g., +1 or No Change]
        """
        return self._call_api(system_prompt)
    
    def run_espionage(self, player_nation, target_nation, operation_details, turn_number):
        """Handles covert operations narrative."""
        system_prompt = f"Director of Intelligence report for {player_nation.name} against {target_nation}. Operation details: {operation_details}"
        return self._call_api(system_prompt)

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
        return self._call_api(system_prompt)

    def generate_event(self, nation, year):
        """Generates a significant historical event."""
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
        response_text = self._call_api(system_prompt)
        
        if "[UPLINK ERROR]" in response_text or "[SYSTEM ERROR]" in response_text:
            return "### GLOBAL EVENT DELAYED\nDue to dense fog of war and global communications gridlock, this year's historical events remain unrecorded. The simulation continues."
            
        return response_text

    def generate_war_report(self, player_nation, target_nation, war_results, current_year):
        """Takes Python's deterministic math and writes a narrative battlefield report, locked to the current game year."""
        system_prompt = f"""
        You are the Supreme Commander of {player_nation}'s Armed Forces in the year {current_year}.
        
        We have just engaged in a massive war against {target_nation}.
        Here is the mathematically determined outcome from the simulation engine:
        - Result: {war_results['result']}
        - Our Combat Power on the field: {war_results['player_power']}
        - Enemy Combat Power on the field: {war_results['enemy_power']}
        - Treasury Cost: ${war_results['cost_billions']:.2f} Billion
        
        Write a thrilling, realistic 2-paragraph military After Action Report (AAR) summarizing the campaign, the tactics used, and the aftermath. 
        
        CRITICAL: Ensure all dates in the report match the year {current_year}. Frame the narrative to match the {war_results['result']} using military terminology appropriate for the year {current_year}.
        CRITICAL: Output ONLY pure Markdown text. Do NOT output JSON.
        """
        return self._call_api(system_prompt)