# core/engine.py
import json
import os
from systems.events import trigger_historical_event
from systems.stat_extractor import apply_ai_stats
from core.ai_handler import AIHandler

class GameEngine:
    def __init__(self, player_nation):
        self.nation = player_nation
        # Set the starting year to whatever the player typed in!
        self.turn_number = self.nation.starting_year 
        self.is_running = True

    def run(self):
        """The main interactive game loop."""
        print(f"\n--- Entering Simulation: Year {self.turn_number} ---")
        
        while self.is_running:
            # The standard user prompt based on the design doc [cite: 298]
            command = input("\nWhat is your next directive? (Type 'help' for options): ").strip()
            
            # Prevent empty inputs from crashing the loop
            if not command:
                continue
                
            self.process_command(command)

    def process_command(self, command):
        lower_command = command.lower()

        if lower_command == 'end turn':
            print(f"\nExecuting end of year protocols for {self.turn_number}...")
            
            event = trigger_historical_event(self.nation, self.turn_number, self.ai)
            if event:
                print("\n" + "!"*50)
                print(" GLOBAL EVENT ALERT")
                print("!"*50)
                print(event)
                print("!"*50 + "\n")
                # Apply the event's math to the stats!
                from systems.stat_extractor import apply_ai_stats
                apply_ai_stats(self.nation, event)

            self.nation.process_turn()
            self.turn_number += 1
            print(f"\n--- Entering Simulation: Year {self.turn_number} ---")
        
        # --- NEW DIPLOMACY SYSTEM [cite: 108-111] ---
        elif lower_command.startswith('diplomacy '):
            target_nation = command.split(" ", 1)[1].strip()
            print(f"\n[SYSTEM LOG]: Establishing secure diplomatic channel with {target_nation}...")
            print(f"[SYSTEM LOG]: Channel open. Type 'exit' to end negotiations.")
            print("="*50)
            
            chat_history = [] # Keeps track of the back-and-forth
            
            # The Diplomacy Sub-Loop
            while True:
                player_message = input(f"\n[You -> {target_nation}]: ").strip()
                
                if player_message.lower() == 'exit':
                    print(f"\n[SYSTEM LOG]: Severing diplomatic connection with {target_nation}.")
                    print("="*50)
                    # Log the meeting in the nation's history
                    self.nation.add_event(self.turn_number, f"Held diplomatic negotiations with {target_nation}.")
                    break
                    
                if not player_message:
                    continue
                
                # Get the AI delegate's response [cite: 115-116]
                print(f"[{target_nation} is typing...]")
                delegate_response = self.ai.negotiate(self.nation.name, target_nation, player_message, chat_history)
                
                print(f"\n[{target_nation} Delegate]: {delegate_response}")
                
                # Save to local history so the AI remembers the flow of the conversation
                chat_history.append(("Supreme Leader", player_message))
                chat_history.append((f"{target_nation} Delegate", delegate_response))
            
        elif lower_command in ['status', 'report']:
            self.nation.display_briefing()
        
        # --- NEW ESPIONAGE SYSTEM  ---
        elif lower_command.startswith('covert '):
            try:
                # Expecting format: covert [Target Nation] - [Operation Details]
                parts = command.split(" ", 1)[1].split("-", 1)
                target_nation = parts[0].strip()
                operation_details = parts[1].strip()
                
                print(f"\n[CLASSIFIED]: Initiating Operation Blacklight against {target_nation}...")
                print("[CLASSIFIED]: Awaiting field report from agents...")
                
                intel_report = self.ai.run_espionage(self.nation, target_nation, operation_details, self.turn_number)
                
                print("\n" + "="*50)
                print(" TOP SECRET: INTELLIGENCE BRIEFING")
                print("="*50)
                print(intel_report)
                print("="*50 + "\n")
                
                # Log the op in history
                self.nation.add_event(self.turn_number, f"[CLASSIFIED] Conducted covert op against {target_nation}: {operation_details}")
                
            except IndexError:
                print("\n[SYSTEM ERROR]: Invalid covert command format.")
                print("Correct format: covert [Target Nation] - [Operation Details]")
            
        # --- MULTI-SAVE SYSTEM ---
        elif lower_command == 'save':
            # Create saves folder if it doesn't exist
            if not os.path.exists("saves"):
                os.makedirs("saves")
            
            # Format: saves/Japan_1910.json
            filename = f"saves/{self.nation.name}_{self.nation.starting_year}.json".replace(" ", "_")
            
            save_data = {
                "turn_number": self.turn_number,
                "nation": self.nation.to_dict()
            }
            
            with open(filename, "w") as f:
                json.dump(save_data, f, indent=4)
            print(f"\n[SYSTEM LOG]: Game state archived as '{filename}'.")

        elif lower_command == 'load':
            if not os.path.exists("saves"):
                print("[SYSTEM LOG]: No save directory found.")
                return

            saves = [f for f in os.listdir("saves") if f.endswith('.json')]
            if not saves:
                print("[SYSTEM LOG]: No save files found.")
                return

            print("\n--- Available Save Slots ---")
            for i, s in enumerate(saves):
                print(f"{i+1}. {s}")
            
            choice = input("\nSelect a slot number to load: ").strip()
            try:
                selected_save = saves[int(choice)-1]
                with open(f"saves/{selected_save}", "r") as f:
                    save_data = json.load(f)
                
                self.turn_number = save_data["turn_number"]
                self.nation = self.nation.__class__.from_dict(save_data["nation"])
                print(f"\n[SYSTEM LOG]: Successfully loaded {selected_save}. Welcome back, Leader.")
                self.nation.display_briefing()
            except (ValueError, IndexError):
                print("[SYSTEM LOG]: Invalid selection.")
                
        elif lower_command == 'help':
            print("\nAvailable System Directives:")
            print(" - 'status'   : View current national statistics.")
            print(" - 'end turn' : Advance time and calculate growth.")
            print(" - 'save'     : Save current progress and history locally.")
            print(" - 'load'     : Load a previously saved session.")
            print(" - 'diplomacy [Nation]': Open a direct negotiation channel with another country.")
            print(" - 'covert [Nation] - [Details]': Launch a classified espionage operation.")
            print(" - 'quit'     : Exit the simulation.")
            print(" * Note: Type any other text to issue a Supreme Leader directive to the AI.")
            
        elif lower_command == 'quit':
            print("Exiting Nacio simulation. Goodbye, Leader.")
            self.is_running = False
            
        else:
            print(f"\n[SYSTEM LOG]: Routing directive to AI for simulation analysis...")
            
            # Notice we pass the whole nation now, not just the name, so the AI gets the history!
            ai_report = self.ai.parse_directive(command, self.nation, self.turn_number)
            
            print("\n" + "="*50)
            print(" AI SIMULATION REPORT")
            print("="*50)
            print(ai_report)
            print("="*50 + "\n")
            
            apply_ai_stats(self.nation, ai_report)
            
            # --- NEW: LOG THE EVENT IN HISTORY ---
            self.nation.add_event(self.turn_number, command)
            print("[SYSTEM LOG]: Directive logged into National History Archives.")