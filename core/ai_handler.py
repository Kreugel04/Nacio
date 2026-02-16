# core/ai_handler.py
import json
import time
import re
import os
from google import genai
from dotenv import load_dotenv

class AIHandler:
    def __init__(self):
        """Initializes the AI connection using the API key from the .env file."""
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        
        if not api_key:
            raise ValueError("API Key not found! Please check your .env file.")
            
        # Updated to the new google.genai client format
        self.client = genai.Client(api_key=api_key)
    
    def generate_starting_nation(self, country_name, year):
        """Asks the AI to generate historically accurate starting stats and a briefing."""
        archive_path = "historical_archive.json"
        lookup_key = f"{country_name}-{year}"

        # 1. Check the local archive first to save API quota
        if os.path.exists(archive_path):
            with open(archive_path, "r") as f:
                archive = json.load(f)
                if lookup_key in archive:
                    print(f"[SYSTEM LOG]: Retrieving {lookup_key} from local historical archives...")
                    return archive[lookup_key]

        # 2. If not found, call the AI
        print(f"[SYSTEM LOG]: {lookup_key} not in archives. Requesting AI generation...")
        
        system_prompt = f"""
        You are the world-building engine for 'Nacio: A Global Symphony'.
        The player has chosen to play as {country_name} in the year {year}.
        
        Based on real-world historical data for {year}, provide realistic starting statistics for {country_name}.
        Write a 2-paragraph 'Initial Cabinet Report' describing the immediate challenges they face at that exact time.
        
        CRITICAL: You must also generate the historical Top 10 highest GDPs and Top 10 strongest Militaries in the world for the year {year}. Exclude {country_name} from these lists.
        
        Respond ONLY in valid JSON format using this exact schema:
        {{
            "population": [integer],
            "gdp": [float, in billions USD],
            "military_strength": [float, 0-1000 scale],
            "political_stability": [float, 0-100 scale],
            "briefing": "[2-paragraph narrative]",
            "world_gdp": {{"Country A": 1000.0, "Country B": 800.0}},
            "world_military": {{"Country A": 950.0, "Country B": 900.0}}
        }}
        """
        
        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=system_prompt
            )
            
            # Clean up potential markdown formatting
            raw_text = response.text.strip()
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:-3].strip()
            elif raw_text.startswith("```"):
                raw_text = raw_text[3:-3].strip()
                
            data = json.loads(raw_text)

            # --- SAVE TO ARCHIVE (Inside Try Block) ---
            if data:
                # Ensure the archive file exists
                if not os.path.exists(archive_path):
                    with open(archive_path, "w") as f:
                        json.dump({}, f)

                # Open and update the archive
                with open(archive_path, "r+") as f:
                    archive = json.load(f)
                    archive[lookup_key] = data
                    f.seek(0)
                    json.dump(archive, f, indent=4)
                    f.truncate()
                
                print(f"[SYSTEM LOG]: {lookup_key} has been saved to the historical archive.")
                return data

        except Exception as e:
            # Handle rate limits (429) or parsing errors
            print(f"\n[AI WORLD-BUILDER ERROR]: {str(e)}")
            return None
        
        return None
    
    def parse_directive(self, directive_text, nation, turn_number):
        """Sends the player's directive to the AI with historical context and auto-retry."""
        
        history_text = "None yet."
        if nation.history:
            history_text = "\n".join([f"Year {event['year']}: {event['directive']}" for event in nation.history[-5:]])

        system_prompt = f"""
        You are the backend simulation engine for a geopolitical game called 'Nations: A Global Symphony'.
        The player is the Supreme Leader of {nation.name}. It is currently Year {turn_number}.
        
        --- RECENT NATIONAL HISTORY ---
        {history_text}
        -------------------------------
        
        The player has issued the following directive: "{directive_text}"
        
        Cross-reference the player's new directive with their recent national history. 
        You must analyze this directive and output the results EXACTLY in the following format. 
        Do not add conversational filler.
        
        Directive Type: [Identify the type, e.g., Law/Project/Diplomacy]
        Command Type: [Summarize the command]
        Target: [Entity affected]
        Risk Profile: [Low/Medium/High with a brief 1-sentence explanation]
        Objective: [What this achieves]
        Advisor Feedback: [1 sentence of advice from a relevant minister]
        
        Execution & Initial Outcomes:
        Related Entity: [Brief outcome description]
        Related Entity: [Brief outcome description]
        
        Statistical Updates:
        (Note: You MUST map your outcomes ONLY to these exact stat names: Population, GDP, Treasury, Military Strength, Political Stability, Public Approval. Format as 'Stat Name: +X%' or 'Stat Name: -X')
        * CRITICAL FINANCIAL RULE: If the player explicitly allocates a specific budget (e.g., $1 Billion, $2 Million), you MUST deduct that exact amount from the 'Treasury' stat in Billions (e.g., $1 Billion is 'Treasury: -1.0', $2 Million is 'Treasury: -0.002').
        [Stat Name]: [Predicted change]
        [Stat Name]: [Predicted change]
        
        Factional Reactions:
        [Faction Name]: [Reaction summary] (Support Change: [+/-X])
        [Faction Name]: [Reaction summary] (Support Change: [+/-X])
        
        Global Reactions Simulated:
        [Country/Bloc]: [Reaction summary]
        [Country/Bloc]: [Reaction summary]
        """
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=system_prompt
                )
                
                # Safety Filter Check
                if not response.candidates or not response.candidates[0].content.parts:
                    return "[CLASSIFIED ALERT]: Directive transmission blocked by international monitors. (AI Safety Filter Triggered: Try rewording your directive)."
                    
                result_text = response.text.strip()
                if not result_text:
                    return "[SYSTEM ERROR]: The AI generated an empty report."
                    
                return result_text
                
            except Exception as e:
                error_msg = str(e)
                # If we hit the rate limit, wait and retry
                if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                    wait_time = 20 * (attempt + 1) # Waits 20s, then 40s, then 60s
                    print(f"\n[SYSTEM LOG]: API Rate Limit hit. Automatically retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    return f"[COMMUNICATIONS UPLINK ERROR]: {error_msg}"
                    
        return "[COMMUNICATIONS UPLINK ERROR]: Maximum retries reached. Please wait a full minute and try your directive again."
        
    def negotiate(self, player_nation_name, target_nation, player_message, chat_history):
        """
        Acts as the interactive diplomat for a foreign nation .
        """
        # Format the ongoing conversation history
        history_text = ""
        for role, text in chat_history:
            history_text += f"{role}: {text}\n"

        system_prompt = f"""
        You are the Chief Diplomatic Delegate for {target_nation}.
        You are currently in direct negotiations with the Supreme Leader of {player_nation_name}.
        
        Your national personality is context-dependent based on real-world historical geopolitical stances, 
        but you must fiercely protect the national interests of {target_nation}[cite: 119].
        
        --- ONGOING CONVERSATION ---
        {history_text}
        Supreme Leader of {player_nation_name}: {player_message}
        ----------------------------
        
        Respond directly to the Supreme Leader in the first-person as the delegate of {target_nation}. 
        Be realistic, nuanced, and maintain a diplomatic tone (which can range from cordial to hostile depending on the request)[cite: 118, 120]. 
        Do NOT output simulation stats or frameworks. Just output your conversational dialogue.
        """
        
    def run_espionage(self, player_nation, target_nation, operation_details, turn_number):
        """
        Handles the risk and narrative generation of covert operations .
        """
        system_prompt = f"""
        You are the Director of Intelligence for {player_nation.name}. It is Year {turn_number}.
        The Supreme Leader has ordered a covert operation against {target_nation}.
        
        Operation Details: "{operation_details}"
        Our Espionage Network Strength: {player_nation.espionage_network}/100
        Our Intelligence Budget: ${player_nation.intelligence_budget}B
        
        Based on our network strength and the ambition of the operation, determine the outcome.
        Operations can be categorized as: Intelligence Gathering, Sabotage, Propaganda, or Assassination.
        
        You MUST output your report EXACTLY in this format:
        
        Operation Type: [Categorize the op]
        Risk Level: [Low/Medium/High/Extreme]
        Outcome: [SUCCESS / PARTIAL SUCCESS / FAILURE / COMPROMISED]
        
        Narrative Report:
        [Write a 2-paragraph highly classified briefing on how the operation unfolded, what was discovered or destroyed, and if our agents were caught or left traces.]
        
        Fallout:
        [If compromised, describe the immediate diplomatic anger from {target_nation}. If successful, describe the secret advantage gained.]
        """
        
        try:
            response = self.client.models.generate_content(
                model='gemini-1.5-flash',
                contents=system_prompt
            )
            return response.text.strip()
        except Exception as e:
            return f"[INTELLIGENCE UPLINK ERROR]: {str(e)}"
    
    def generate_event(self, nation, year):
        """Generates a real-world historical event matching the current year."""
        
        # Stop generating events if we hit the current day (2026)
        if year >= 2026:
            return None

        system_prompt = f"""
        You are the Historical Chronicler for Nacio. The current year is {year}.
        The player is leading {nation.name}. 
        
        Identify a SIGNIFICANT REAL-WORLD HISTORICAL EVENT that occurred in {year}.
        If {year} was a year of a major ongoing conflict (like WWII or the Cold War), 
        describe a specific milestone or shift from that year.
        
        Analyze how this event specifically impacts {nation.name} based on its current stats and history.
        
        Output format:
        Event Title: [Official Historical Name]
        Historical Context: [2-3 sentences explaining the global situation in {year}]
        Impact on {nation.name}: [How this specifically affects the player's country]
        
        Statistical Updates:
        (Use only: Population, GDP, Military Strength, Political Stability, Public Approval)
        [Stat Name]: [Change, e.g., -5% or +10.0]
        
        Factional Reactions:
        (Support Change: +/-X)
        [Faction Name]: [Reaction] (Support Change: [+/-X])
        """
        
        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=system_prompt
            )
            return response.text.strip()
        except Exception as e:
            return f"[HISTORICAL LOG ERROR]: {str(e)}"
        
        